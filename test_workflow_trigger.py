#!/usr/bin/env python3
"""
Test script to simulate different scenarios for workflow trigger logic.
"""

import json
import os
import shutil
import sys
from helpers import track_changes

def backup_data():
    """Backup current data files"""
    shutil.copy("data/current_data.json", "data/current_data.json.backup")
    print("✅ Backed up current_data.json")

def restore_data():
    """Restore data from backup"""
    shutil.copy("data/current_data.json.backup", "data/current_data.json")
    print("✅ Restored current_data.json from backup")

def clean_trigger_file():
    """Remove trigger file if it exists"""
    if os.path.exists("data/workflow_trigger"):
        os.remove("data/workflow_trigger")

def test_trigger_logic(current_data, previous_data, scenario_name):
    """Test the trigger logic for given data"""
    print(f"\n🧪 Testing scenario: {scenario_name}")
    
    # Track changes
    changes = track_changes(current_data, previous_data)
    
    # Categorize changes (same logic as parser.py)
    has_new = any("current_offer" in change and "previous_offer" not in change for change in changes)
    has_removed = any("previous_offer" in change and "current_offer" not in change for change in changes)
    has_price_changes = any("current_offer" in change and "previous_offer" in change for change in changes)
    
    # Count changes by type
    new_count = sum(1 for change in changes if "current_offer" in change and "previous_offer" not in change)
    removed_count = sum(1 for change in changes if "previous_offer" in change and "current_offer" not in change)
    price_count = sum(1 for change in changes if "current_offer" in change and "previous_offer" in change)
    
    print(f"📊 Changes detected:")
    print(f"   - New offers: {new_count}")
    print(f"   - Removed offers: {removed_count}")
    print(f"   - Price changes: {price_count}")
    
    # Simulate the trigger logic from parser.py
    clean_trigger_file()
    os.makedirs("data", exist_ok=True)
    
    if has_removed:
        with open("data/workflow_trigger", "w") as f:
            f.write("mode=update\nsearch=narrow")
        print("✅ Created trigger file: mode=update search=narrow")
    elif has_new or has_price_changes:
        with open("data/workflow_trigger", "w") as f:
            f.write("mode=new\nsearch=narrow")
        print("✅ Created trigger file: mode=new search=narrow")
    else:
        print("❌ No trigger file created (no changes)")
    
    # Check if trigger file exists
    if os.path.exists("data/workflow_trigger"):
        with open("data/workflow_trigger", "r") as f:
            trigger_content = f.read()
        print(f"📄 Trigger file content:\n{trigger_content}")
    else:
        print("📄 No trigger file found")
    
    return os.path.exists("data/workflow_trigger")

def main():
    """Run all test scenarios"""
    print("🚀 Starting workflow trigger logic tests")
    
    # Backup current data
    backup_data()
    
    try:
        # Load current data
        with open("data/current_data.json", "r") as f:
            current_data = json.load(f)
        
        print(f"📈 Current data has {len(current_data)} offers")
        
        # Test Scenario 1: No changes
        print("\n" + "="*60)
        test_trigger_logic(current_data, current_data, "No changes")
        
        # Test Scenario 2: Removed offers
        print("\n" + "="*60)
        previous_data_with_extra = current_data.copy()
        # Add a fake offer to simulate removal
        fake_offer = {
            "offer_id": "test_removed_offer",
            "price": "100000 ₽/мес.",
            "price_numeric": 100000,
            "title": "Test Removed Offer",
            "metro": "Test Metro",
            "building_id": "test_building",
            "floor": 1,
            "rooms": 1
        }
        previous_data_with_extra.append(fake_offer)
        test_trigger_logic(current_data, previous_data_with_extra, "Removed offers")
        
        # Test Scenario 3: New offers
        print("\n" + "="*60)
        current_data_with_new = current_data.copy()
        # Add a fake new offer
        fake_new_offer = {
            "offer_id": "test_new_offer",
            "price": "200000 ₽/мес.",
            "price_numeric": 200000,
            "title": "Test New Offer",
            "metro": "Test Metro New",
            "building_id": "test_building_new",
            "floor": 2,
            "rooms": 2
        }
        current_data_with_new.append(fake_new_offer)
        test_trigger_logic(current_data_with_new, current_data, "New offers")
        
        # Test Scenario 4: Price changes
        print("\n" + "="*60)
        if current_data:
            import copy
            current_data_with_price_change = copy.deepcopy(current_data)
            previous_data_with_old_price = copy.deepcopy(current_data)
            
            # Modify the first offer's price
            current_data_with_price_change[0]["price"] = "999999 ₽/мес."
            current_data_with_price_change[0]["price_numeric"] = 999999
            previous_data_with_old_price[0]["price"] = "111111 ₽/мес."
            previous_data_with_old_price[0]["price_numeric"] = 111111
            
            test_trigger_logic(current_data_with_price_change, previous_data_with_old_price, "Price changes")
        
        print("\n" + "="*60)
        print("✅ All tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
    
    finally:
        # Restore original data
        restore_data()
        clean_trigger_file()
        print("🧹 Cleaned up test files")

if __name__ == "__main__":
    main()