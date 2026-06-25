import os
import re
import time
import logging
import pandas as pd
import pdfplumber
import openai  # Required for catching the RateLimitError
from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional
from openai import OpenAI
import instructor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("idp_pipeline_v3.log"),
        logging.StreamHandler()
    ]
)

# =====================================================================
# CORE DATA STRUCTURES & ALGORITHMS
# =====================================================================

# Phase 2: Finite State Automata (DFA)
class ParserState(Enum):
    SCAN_HEADER = 1
    READ_TABLE  = 2
    IGNORE_JUNK = 3

# Phase 4: Quadratic Probing Hash Table
class QuadraticHashTable:
    def __init__(self, size=2000):
        self.size  = size
        self.table = [None] * size

    def _hash(self, text: str):
        return sum(ord(c) for c in text) % self.size

    def insert_and_check(self, item: str) -> bool:
        """Returns True if new (inserted), False if duplicate."""
        idx = self._hash(item)
        for i in range(self.size):
            probe = (idx + i ** 2) % self.size
            if self.table[probe] is None:
                self.table[probe] = item
                return True          # new item
            if self.table[probe] == item:
                return False         # duplicate
        return True                  # table full — treat as new (edge case)

# Phase 6: N-ary Trie / Tree Structure
class TreeNode:
    def __init__(self, name: str, is_header: bool = False):
        self.name      = name
        self.is_header = is_header
        self.children  = []          # holds dicts once parts are added

# Updated Cloud Data Schema (Commercial BOM)
class BoMRow(BaseModel):
    sr_no:                  Optional[str] = Field(None, description="Serial number if available")
    cust_part_no:           Optional[str] = Field(None, description="Customer part number")
    rev:                    Optional[str] = Field(None, description="Revision number")
    qty:                    Optional[str] = Field(None, description="Quantity")
    item_name:              str           = Field(...,  description="Short name of the item (e.g., Oil Tank, Air Breather, Gate Valve)")
    technical_specification:str           = Field(...,  description="Full technical details, tank size, dimensions, location, etc.")
    moc:                    Optional[str] = Field(None, description="Material of construction (e.g., SS316, SS304)")
    make:                   Optional[str] = Field(None, description="Manufacturer or brand (e.g., Cenlub Systems, Hawa Engg)")
    unit_price:             Optional[str] = Field(None, description="Numeric unit price if mentioned")
    total_price:            Optional[str] = Field(None, description="Numeric total price if mentioned")
    commercial_remarks:     Optional[str] = Field(None, description="Delivery time, Model, Item code, Offer Ref, etc.")

class BoMChunkResponse(BaseModel):
    parts: List[BoMRow] = Field(..., description="Array of formatted parts")

# =====================================================================
# PIPELINE FUNCTIONS
# =====================================================================

# Phase 3: Regex Demultiplexer
def unroll_multiplexed_string(text: str) -> List[str]:
    """Finds 'Pump 101 A/B/C' and unrolls to ['Pump 101 A', 'Pump 101 B', 'Pump 101 C']"""
    match = re.search(r'(.*?)\s+([A-Z](?:/[A-Z])+)(.*)', text)
    if match:
        base     = match.group(1).strip()
        variants = match.group(2).split('/')
        tail     = match.group(3).strip()
        return [f"{base} {v} {tail}".strip() for v in variants]
    return [text]

# Phase 5: BiLSTM Engine (Local Brain Placeholder)
def local_ner_tagger(text: str) -> str:
    """PLACEHOLDER: Replace with your PyTorch/TensorFlow BiLSTM model here."""
    return text.strip()


def run_advanced_pipeline(folder_path: str, output_path: str, groq_api_key: str):

    # Ensure directories exist
    os.makedirs(folder_path, exist_ok=True)

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    client = instructor.from_openai(
        OpenAI(base_url="https://api.groq.com/openai/v1", api_key=groq_api_key),
        mode=instructor.Mode.JSON
    )

    pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
    if not pdf_files:
        print(f"[ERROR] No PDFs found in {folder_path}. Please add files and run again.")
        return

    current_state    = ParserState.SCAN_HEADER
    memory_tree_root = TreeNode("DOCUMENT_ROOT")

    default_node     = TreeNode("UNCLASSIFIED_ITEMS", is_header=True)
    memory_tree_root.children.append(default_node)
    current_parent_node = default_node          

    cache           = QuadraticHashTable()
    successful_pdfs = set()

    checkpoint_file = os.path.join(folder_path, "temp_checkpoint.csv")
    checkpoint_cols = [
        "ASSEMBLY_SYSTEM", "SR. NO.", "CUST. PART. NO.", "REV.", "QTY",
        "ITEM_NAME", "TECHNICAL SPECIFICATION", "MOC", "MAKE",
        "UNIT PRICE", "TOTAL PRICE", "COMMERCIAL DETAILS", "Traceability"
    ]
    pd.DataFrame(columns=checkpoint_cols).to_csv(checkpoint_file, index=False)

    print(f"\n[PHASE 1] Extracting & Filtering {len(pdf_files)} files...")

    # Phase 1: Raw Extraction
    for filename in pdf_files:
        try:
            with pdfplumber.open(os.path.join(folder_path, filename)) as pdf:
                for page_idx, page in enumerate(pdf.pages):
                    tables = page.extract_tables()
                    if not tables:
                        continue

                    for table in tables:
                        df = pd.DataFrame(table).dropna(how='all')
                        for _, row in df.iterrows():
                            val = " | ".join(
                                [str(v).strip() for v in row if v and str(v).strip() != '']
                            )
                            if not val:
                                continue

                            # Phase 2: Finite State Automata (The Bouncer)
                            junk_keywords = ["SCALE", "PROJECTION", "P&ID", "CONFIDENTIAL", "REV NO"]
                            if any(j in val.upper() for j in junk_keywords):
                                current_state = ParserState.IGNORE_JUNK
                                continue

                            if len(val) > 100:
                                continue

                            # Heuristic: all-uppercase short text with no pipe = equipment header
                            if val.isupper() and len(val) < 40 and "|" not in val:
                                current_state = ParserState.SCAN_HEADER
                            else:
                                current_state = ParserState.READ_TABLE

                            if current_state == ParserState.SCAN_HEADER:
                                new_header = TreeNode(val, is_header=True)
                                memory_tree_root.children.append(new_header)  
                                current_parent_node = new_header
                                cache = QuadraticHashTable()                  

                            elif current_state == ParserState.READ_TABLE:
                                # Phase 3: Regex Demultiplexer
                                unrolled_items = unroll_multiplexed_string(val)

                                for item in unrolled_items:
                                    # Phase 4: Quadratic Hashing
                                    if cache.insert_and_check(item):
                                        # Phase 5: BiLSTM NER
                                        tagged_item = local_ner_tagger(item)
                                        # Phase 6: Tree Construction 
                                        current_parent_node.children.append({
                                            "data":  tagged_item,
                                            "trace": f"{filename} | Pg {page_idx + 1}"
                                        })
                                        successful_pdfs.add(filename)

        except Exception as e:
            logging.error(f"Failed parsing {filename}: {e}")

    # Phase 7: Semantic Chunking
    chunks = [
        node for node in memory_tree_root.children
        if isinstance(node, TreeNode) and node.children   
    ]

    print(f"\n[PHASE 2 & 3] Tree Built. Found {len(chunks)} Equipment Branch(es).")

    # Phase 8: Map-Reduce via Groq with Dynamic Rate Limit Handling
    print("\n[STARTING CLOUD MAP-REDUCE]")
    final_dfs = []

    for idx, branch in enumerate(chunks):
        print(f"\n=======================================================")
        print(f"Mapping Branch {idx + 1}/{len(chunks)}: {branch.name}")
        
        dict_children = [c for c in branch.children if isinstance(c, dict)]
        if not dict_children:
            continue

        # Keep batches small so the JSON output doesn't get cut off
        BATCH_SIZE = 15 
        branch_rows = []
        total_batches = (len(dict_children) + BATCH_SIZE - 1) // BATCH_SIZE

        for i in range(0, len(dict_children), BATCH_SIZE):
            current_batch_num = (i // BATCH_SIZE) + 1
            print(f"  -> Sending Batch {current_batch_num} of {total_batches}...")
            
            batch = dict_children[i:i + BATCH_SIZE]
            raw_items  = [child["data"] for child in batch]
            trace_data = batch[0].get("trace", "Unknown")

            prompt = (
                f"Equipment System: {branch.name}\n"
                f"Extract these items into the schema:\n"
                + "\n".join(raw_items)
            )

            # --- DYNAMIC WAIT LOGIC ---
            while True:
                try:
                    response = client.chat.completions.create(
                        model          = "llama-3.1-8b-instant",
                        response_model = BoMChunkResponse,
                        temperature    = 0.0,
                        max_tokens     = 4096,
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "You are a precise engineering parser. "
                                    "Separate Material (MOC), Manufacturer (MAKE), and Technical Specs "
                                    "into their exact fields. Do not lump them together."
                                )
                            },
                            {"role": "user", "content": prompt}
                        ]
                    )

                    for part in response.parts:
                        branch_rows.append({
                            "ASSEMBLY_SYSTEM":        branch.name,
                            "SR. NO.":                part.sr_no,
                            "CUST. PART. NO.":        part.cust_part_no,
                            "REV.":                   part.rev,
                            "QTY":                    part.qty,
                            "ITEM_NAME":              part.item_name,
                            "TECHNICAL SPECIFICATION":part.technical_specification,
                            "MOC":                    part.moc,
                            "MAKE":                   part.make,
                            "UNIT PRICE":             part.unit_price,
                            "TOTAL PRICE":            part.total_price,
                            "COMMERCIAL DETAILS":     part.commercial_remarks,
                            "Traceability":           trace_data
                        })
                    
                    print(f"  ✓ Batch {current_batch_num} processed successfully.")
                    time.sleep(2)  # Tiny 2-second breather between successful calls
                    break          # Break out of the retry loop and move to the next batch

                except openai.RateLimitError:
                    # If Groq says "Too Many Requests", we catch it, wait 60s, and the while loop retries
                    print(f"  [!] Rate Limit Reached. Pausing for 60 seconds to clear Groq's queue...")
                    time.sleep(60)
                    print(f"  [+] Resuming Batch {current_batch_num}...")
                
                except Exception as e:
                    # If it's a different error (like a parsing issue), log it and move on
                    logging.warning(f"\n  [!] Failed to process Batch {current_batch_num} in '{branch.name}': {e}")
                    break          # Break the while loop to prevent infinite crashing
            # -------------------------------------------

        # Append data from all batches in this branch
        if branch_rows:
            df_chunk = pd.DataFrame(branch_rows)
            final_dfs.append(df_chunk)

            # Phase 9: Iterative Checkpointing
            df_chunk.to_csv(checkpoint_file, mode='a', header=False, index=False)

    # Phase 10: Flatten, Export & Summary
    if final_dfs:
        master_df = pd.concat(final_dfs, ignore_index=True)
        master_df.to_excel(output_path, index=False)

        print("\n" + "=" * 50)
        print("PIPELINE COMPLETION SUMMARY")
        print("=" * 50)
        print(f"Total PDFs Found:     {len(pdf_files)}")
        print(f"PDFs Processed:       {len(successful_pdfs)}")
        print(f"Total Branches Built: {len(chunks)}")
        print(f"Total Rows Exported:  {len(master_df)}")
        print(f"Master BOM Saved To:  {output_path}")
        print("=" * 50 + "\n")
    else:
        print("\n[WARNING] Pipeline finished but no data was successfully mapped.")


if __name__ == "__main__":
    YOUR_API_KEY = "YOUR_API_KEY_HERE"

    run_advanced_pipeline(
        folder_path  = "D:\\AI_RMC_Project\\Input_PDFs",
        output_path  = "D:\\AI_RMC_Project\\Output_BOMs\\MASTER_CLIENT_BOM_V3.xlsx",
        groq_api_key = YOUR_API_KEY
    )