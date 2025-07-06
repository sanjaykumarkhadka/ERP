-- =====================================================
-- DATABASE SCHEMA MIGRATION SCRIPT
-- From Current Schema to New Manufacturing Design
-- =====================================================
-- This migration implements the new two-table design:
-- 1. Simplified item_master with self-referencing FKs
-- 2. New recipe_components table for BOM relationships
-- =====================================================

-- =====================================================
-- STEP 1: CREATE BACKUP TABLES
-- =====================================================

-- Backup current data before migration
CREATE TABLE item_master_backup AS SELECT * FROM item_master;
CREATE TABLE recipe_master_backup AS SELECT * FROM recipe_master;

-- =====================================================
-- STEP 2: ADD NEW COLUMNS TO ITEM_MASTER
-- =====================================================

-- Add item_type as direct string column (removing FK dependency)
ALTER TABLE item_master ADD COLUMN item_type VARCHAR(20);

-- Add self-referencing foreign keys for FG composition
ALTER TABLE item_master ADD COLUMN wip_item_id INT NULL;
ALTER TABLE item_master ADD COLUMN wipf_item_id INT NULL;

-- Rename columns to match new requirements
ALTER TABLE item_master CHANGE COLUMN min_level min_stock DECIMAL(10,2);
ALTER TABLE item_master CHANGE COLUMN max_level max_stock DECIMAL(10,2);

-- =====================================================
-- STEP 3: POPULATE ITEM_TYPE COLUMN
-- =====================================================

-- Migrate item types from lookup table to direct string
UPDATE item_master im 
JOIN item_type it ON im.item_type_id = it.id 
SET im.item_type = it.type_name;

-- Add Packaging type if it doesn't exist
UPDATE item_master SET item_type = 'Packaging' 
WHERE item_code LIKE 'PKG%' OR description LIKE '%packaging%' OR description LIKE '%package%';

-- =====================================================
-- STEP 4: CREATE NEW RECIPE_COMPONENTS TABLE
-- =====================================================

CREATE TABLE recipe_components (
    id INT PRIMARY KEY AUTO_INCREMENT,
    
    -- The WIP item being produced (recipe output)
    wip_item_id INT NOT NULL,
    
    -- The Raw Material component required (recipe input)
    rm_item_id INT NOT NULL,
    
    -- Quantity of this RM needed to make the WIP
    quantity_kg DECIMAL(10,3) NOT NULL,
    
    -- Optional recipe metadata
    recipe_code VARCHAR(50),
    step_order INT DEFAULT 1,
    notes TEXT,
    
    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    FOREIGN KEY (wip_item_id) REFERENCES item_master(id) ON DELETE CASCADE,
    FOREIGN KEY (rm_item_id) REFERENCES item_master(id) ON DELETE CASCADE,
    
    -- Business rule constraints
    CHECK (quantity_kg > 0),
    
    -- Ensure no duplicate RM in same WIP recipe
    UNIQUE(wip_item_id, rm_item_id)
);

-- =====================================================
-- STEP 5: MIGRATE RECIPE DATA
-- =====================================================

-- Migrate existing recipe data to new structure
-- Only migrate recipes where finished_good is WIP type
INSERT INTO recipe_components (wip_item_id, rm_item_id, quantity_kg, recipe_code, created_at)
SELECT 
    rm.finished_good_id as wip_item_id,
    rm.raw_material_id as rm_item_id,
    rm.kg_per_batch as quantity_kg,
    rm.recipe_code,
    rm.created_at
FROM recipe_master rm
JOIN item_master im ON rm.finished_good_id = im.id
WHERE im.item_type = 'WIP';

-- =====================================================
-- STEP 6: POPULATE FG COMPOSITION COLUMNS
-- =====================================================

-- For FG items, populate wip_item_id based on existing recipe relationships
-- This requires business logic - you may need to adjust based on your data

-- Example: If FG items have recipes pointing to WIP items
UPDATE item_master fg
SET wip_item_id = (
    SELECT DISTINCT rm.finished_good_id 
    FROM recipe_master rm 
    JOIN item_master wip ON rm.finished_good_id = wip.id
    WHERE rm.raw_material_id = fg.id 
    AND wip.item_type = 'WIP'
    LIMIT 1
)
WHERE fg.item_type = 'FG';

-- For FG items that use WIPF, populate wipf_item_id
-- This needs to be done based on your business rules
UPDATE item_master fg
SET wipf_item_id = (
    SELECT DISTINCT rm.finished_good_id 
    FROM recipe_master rm 
    JOIN item_master wipf ON rm.finished_good_id = wipf.id
    WHERE rm.raw_material_id = fg.id 
    AND wipf.item_type = 'WIPF'
    LIMIT 1
)
WHERE fg.item_type = 'FG';

-- =====================================================
-- STEP 7: ADD FOREIGN KEY CONSTRAINTS
-- =====================================================

-- Add self-referencing foreign key constraints
ALTER TABLE item_master 
ADD CONSTRAINT fk_item_master_wip 
FOREIGN KEY (wip_item_id) REFERENCES item_master(id);

ALTER TABLE item_master 
ADD CONSTRAINT fk_item_master_wipf 
FOREIGN KEY (wipf_item_id) REFERENCES item_master(id);

-- =====================================================
-- STEP 8: ADD BUSINESS RULE CONSTRAINTS
-- =====================================================

-- Ensure only FG items can have wip_item_id or wipf_item_id
ALTER TABLE item_master 
ADD CONSTRAINT chk_fg_composition 
CHECK (
    (item_type = 'FG' AND wip_item_id IS NOT NULL) 
    OR 
    (item_type != 'FG' AND wip_item_id IS NULL AND wipf_item_id IS NULL)
);

-- =====================================================
-- STEP 9: CREATE INDEXES FOR PERFORMANCE
-- =====================================================

-- Primary lookup indexes
CREATE INDEX idx_item_master_type ON item_master(item_type);
CREATE INDEX idx_item_master_code ON item_master(item_code);
CREATE INDEX idx_item_master_active ON item_master(is_active);

-- Composition relationship indexes
CREATE INDEX idx_item_master_wip_ref ON item_master(wip_item_id);
CREATE INDEX idx_item_master_wipf_ref ON item_master(wipf_item_id);

-- Recipe component indexes
CREATE INDEX idx_recipe_components_wip ON recipe_components(wip_item_id);
CREATE INDEX idx_recipe_components_rm ON recipe_components(rm_item_id);
CREATE INDEX idx_recipe_components_code ON recipe_components(recipe_code);

-- =====================================================
-- STEP 10: CLEAN UP OLD STRUCTURE
-- =====================================================

-- Remove old foreign key constraint to item_type table
ALTER TABLE item_master DROP FOREIGN KEY item_master_ibfk_1;
ALTER TABLE item_master DROP COLUMN item_type_id;

-- =====================================================
-- STEP 11: INSERT SAMPLE DATA FOR VALIDATION
-- =====================================================

-- Sample Raw Materials
INSERT INTO item_master (item_code, description, item_type, category, price_per_kg, min_stock, max_stock, is_active) VALUES
('RM-PORK', 'Pork Shoulder Premium Grade', 'RM', 'Meat', 8.50, 500, 2000, TRUE),
('RM-SPICE', 'Ham Seasoning Mix', 'RM', 'Spices', 25.00, 50, 200, TRUE);

-- Sample Work-in-Progress item
INSERT INTO item_master (item_code, description, item_type, category, department, machinery, is_active) VALUES
('1003', 'Ham Base - WIP', 'WIP', 'Processed Meat', 'Production', 'Mixer-001', TRUE);

-- Sample Work-in-Progress-Final item
INSERT INTO item_master (item_code, description, item_type, category, department, machinery, is_active) VALUES
('WIPF-SMOKE', 'Smoking Process', 'WIPF', 'Final Processing', 'Smoking Room', 'Smoker-001', TRUE);

-- Sample Finished Goods with composition
INSERT INTO item_master (item_code, description, item_type, category, wip_item_id, wipf_item_id, is_active) VALUES
('1002.1', 'Ham Sliced 200g', 'FG', 'Packaged Meat', 
    (SELECT id FROM item_master WHERE item_code = '1003'), NULL, TRUE),
('1002.2', 'Ham Sliced 500g', 'FG', 'Packaged Meat', 
    (SELECT id FROM item_master WHERE item_code = '1003'), NULL, TRUE),
('1005.1', 'Smoked Ham Sliced 200g', 'FG', 'Premium Packaged Meat', 
    (SELECT id FROM item_master WHERE item_code = '1003'), 
    (SELECT id FROM item_master WHERE item_code = 'WIPF-SMOKE'), TRUE);

-- Sample Recipe Components
INSERT INTO recipe_components (wip_item_id, rm_item_id, quantity_kg, recipe_code, step_order) VALUES
((SELECT id FROM item_master WHERE item_code = '1003'), 
 (SELECT id FROM item_master WHERE item_code = 'RM-PORK'), 100.000, 'HAM-BASE-001', 1),
((SELECT id FROM item_master WHERE item_code = '1003'), 
 (SELECT id FROM item_master WHERE item_code = 'RM-SPICE'), 25.000, 'HAM-BASE-001', 2);

-- =====================================================
-- VALIDATION QUERIES
-- =====================================================

-- Query 1: Show complete BOM for a finished good
SELECT 
    fg.item_code AS finished_good,
    fg.description AS fg_description,
    wip.item_code AS wip_component,
    wip.description AS wip_description,
    wipf.item_code AS wipf_component,
    wipf.description AS wipf_description,
    rm.item_code AS raw_material,
    rm.description AS rm_description,
    rc.quantity_kg AS rm_quantity_needed
FROM item_master fg
LEFT JOIN item_master wip ON fg.wip_item_id = wip.id
LEFT JOIN item_master wipf ON fg.wipf_item_id = wipf.id
LEFT JOIN recipe_components rc ON wip.id = rc.wip_item_id
LEFT JOIN item_master rm ON rc.rm_item_id = rm.id
WHERE fg.item_type = 'FG'
ORDER BY fg.item_code, rc.step_order;

-- Query 2: Show all finished goods using a specific WIP
SELECT 
    fg.item_code,
    fg.description,
    CASE WHEN fg.wipf_item_id IS NOT NULL THEN 'Yes' ELSE 'No' END AS has_final_processing,
    wipf.item_code AS final_process_step
FROM item_master fg
LEFT JOIN item_master wipf ON fg.wipf_item_id = wipf.id
WHERE fg.wip_item_id = (SELECT id FROM item_master WHERE item_code = '1003');

-- Query 3: Show recipe components for a WIP item
SELECT 
    wip.item_code AS wip_item,
    wip.description AS wip_description,
    rm.item_code AS raw_material,
    rm.description AS rm_description,
    rc.quantity_kg,
    rc.step_order
FROM item_master wip
JOIN recipe_components rc ON wip.id = rc.wip_item_id
JOIN item_master rm ON rc.rm_item_id = rm.id
WHERE wip.item_type = 'WIP'
ORDER BY wip.item_code, rc.step_order;

-- =====================================================
-- MIGRATION COMPLETION NOTES
-- =====================================================

/*
MIGRATION SUMMARY:

1. ✅ Simplified item_master table with direct item_type column
2. ✅ Added self-referencing wip_item_id and wipf_item_id for FG composition
3. ✅ Created new recipe_components table for BOM relationships
4. ✅ Migrated existing recipe data appropriately
5. ✅ Added performance indexes and business rule constraints
6. ✅ Included sample data demonstrating the new structure

POST-MIGRATION TASKS:

1. Update your Flask models to match the new schema
2. Update controllers to use the new table structure
3. Test all BOM explosion and costing queries
4. Verify data integrity with validation queries
5. Update any reports or dashboards using the old structure

BENEFITS OF NEW DESIGN:

- Simplified two-table design reduces complexity
- Self-referencing FKs elegantly handle FG composition
- Direct item_type column improves query performance
- Clear separation between recipes (WIP→RM) and composition (FG→WIP/WIPF)
- Maintains all business rule enforcement through constraints
*/ 