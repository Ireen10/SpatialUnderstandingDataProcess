"""
JSON schema mapping and transformation service
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from datetime import datetime

from app.core.config import settings


class SchemaMappingService:
    """Service for transforming JSON data based on schema mappings."""
    
    def __init__(self):
        self.storage_path = Path(settings.DATA_STORAGE_PATH)
    
    def transform_json(
        self,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        mapping: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Transform JSON data based on field mapping.
        
        Args:
            data: Input JSON data (object or array)
            mapping: Field mapping configuration
            options: Additional options
        
        Returns:
            Transformed JSON data
        
        Mapping format:
        {
            "field_mappings": {
                "source_field": "target_field",
                "old_name": "new_name",
                "nested.path.old": "nested.path.new"
            },
            "value_transforms": {
                "field_name": {
                    "type": "rename_values",
                    "mappings": {"old_val": "new_val"}
                },
                "status_field": {
                    "type": "case",
                    "case": "upper"  # upper, lower, title
                },
                "numeric_field": {
                    "type": "multiply",
                    "factor": 100
                }
            },
            "field_operations": {
                "concat_field": {
                    "type": "concat",
                    "sources": ["field1", "field2"],
                    "separator": " "
                },
                "split_field": {
                    "type": "split",
                    "source": "combined_field",
                    "separator": " ",
                    "targets": ["part1", "part2"]
                },
                "computed_field": {
                    "type": "template",
                    "template": "{prefix}_{suffix}",
                    "fields": {"prefix": "field_a", "suffix": "field_b"}
                }
            },
            "include_fields": ["field1", "field2"],  # Only include these
            "exclude_fields": ["internal_id", "temp"],  # Exclude these
            "add_fields": {  # Add constant fields
                "version": "1.0",
                "source": "my_dataset"
            },
            "nested_flatten": {
                "metadata.width": "width",
                "metadata.height": "height"
            },
            "nested_group": {
                "prefix": "meta",  # Group fields starting with x,y into "meta": {"x":..., "y":...}
                "fields": ["x", "y"]
            }
        }
        """
        options = options or {}
        
        # Handle array
        if isinstance(data, list):
            return [self._transform_object(item, mapping, options) for item in data]
        
        # Handle single object
        return self._transform_object(data, mapping, options)
    
    def _transform_object(
        self,
        obj: Dict[str, Any],
        mapping: Dict[str, Any],
        options: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Transform a single JSON object."""
        result = {}
        
        field_mappings = mapping.get("field_mappings", {})
        value_transforms = mapping.get("value_transforms", {})
        field_operations = mapping.get("field_operations", {})
        include_fields = mapping.get("include_fields")
        exclude_fields = mapping.get("exclude_fields", [])
        add_fields = mapping.get("add_fields", {})
        nested_flatten = mapping.get("nested_flatten", {})
        nested_group = mapping.get("nested_group", {})
        remove_empty = mapping.get("remove_empty", False)
        
        # Start with original data
        working_obj = dict(obj)
        
        # 1. Apply nested flatten first
        for source_path, target_field in nested_flatten.items():
            value = self._get_nested_value(working_obj, source_path)
            if value is not None:
                result[target_field] = value
        
        # 2. Apply field mappings (rename)
        for source_field, target_field in field_mappings.items():
            value = self._get_nested_value(working_obj, source_field)
            if value is not None:
                self._set_nested_value(result, target_field, value)
        
        # 3. Apply field operations
        for target_field, operation in field_operations.items():
            op_type = operation.get("type")
            
            if op_type == "concat":
                values = []
                for src in operation.get("sources", []):
                    val = self._get_nested_value(working_obj, src)
                    if val is not None:
                        values.append(str(val))
                result[target_field] = operation.get("separator", " ").join(values)
            
            elif op_type == "split":
                source = operation.get("source")
                separator = operation.get("separator", " ")
                targets = operation.get("targets", [])
                
                val = self._get_nested_value(working_obj, source)
                if val and isinstance(val, str):
                    parts = val.split(separator)
                    for i, target in enumerate(targets):
                        if i < len(parts):
                            result[target] = parts[i].strip()
            
            elif op_type == "template":
                template = operation.get("template", "")
                fields = operation.get("fields", {})
                
                format_args = {}
                for key, src_field in fields.items():
                    val = self._get_nested_value(working_obj, src_field)
                    format_args[key] = val if val is not None else ""
                
                result[target_field] = template.format(**format_args)
            
            elif op_type == "extract":
                source = operation.get("source")
                pattern = operation.get("pattern")
                import re
                val = self._get_nested_value(working_obj, source)
                if val and isinstance(val, str):
                    match = re.search(pattern, val)
                    if match:
                        result[target_field] = match.group(1) if match.groups() else match.group(0)
        
        # 4. Apply value transforms
        for field_name, transform in value_transforms.items():
            # Get value from result if already transformed, else from original
            value = result.get(field_name)
            if value is None:
                value = self._get_nested_value(working_obj, field_name)
            
            if value is None:
                continue
            
            transform_type = transform.get("type")
            
            if transform_type == "rename_values":
                mappings = transform.get("mappings", {})
                result[field_name] = mappings.get(value, value)
            
            elif transform_type == "case":
                case = transform.get("case", "lower")
                if isinstance(value, str):
                    if case == "upper":
                        result[field_name] = value.upper()
                    elif case == "lower":
                        result[field_name] = value.lower()
                    elif case == "title":
                        result[field_name] = value.title()
            
            elif transform_type == "multiply":
                factor = transform.get("factor", 1)
                if isinstance(value, (int, float)):
                    result[field_name] = value * factor
            
            elif transform_type == "divide":
                factor = transform.get("factor", 1)
                if isinstance(value, (int, float)) and factor != 0:
                    result[field_name] = value / factor
            
            elif transform_type == "round":
                decimals = transform.get("decimals", 0)
                if isinstance(value, (int, float)):
                    result[field_name] = round(value, decimals)
            
            elif transform_type == "type_cast":
                target_type = transform.get("target_type", "string")
                try:
                    if target_type == "int":
                        result[field_name] = int(value)
                    elif target_type == "float":
                        result[field_name] = float(value)
                    elif target_type == "string":
                        result[field_name] = str(value)
                    elif target_type == "bool":
                        result[field_name] = bool(value)
                except (ValueError, TypeError):
                    result[field_name] = value
            
            elif transform_type == "default":
                if value is None or value == "":
                    result[field_name] = transform.get("default_value")
            
            elif transform_type == "regex_replace":
                pattern = transform.get("pattern", "")
                replacement = transform.get("replacement", "")
                if isinstance(value, str):
                    import re
                    result[field_name] = re.sub(pattern, replacement, value)
        
        # 5. Copy remaining fields (if not using include_fields)
        if include_fields is None:
            for key, value in working_obj.items():
                if key not in result and key not in exclude_fields:
                    # Check if this field was already handled
                    if not any(key == src or key in str(src) for src in field_mappings.keys()):
                        if not any(key in nested_flatten.values() for nested_flatten in [nested_flatten]):
                            result[key] = value
        
        # 6. Apply include_fields filter
        if include_fields:
            result = {k: v for k, v in result.items() if k in include_fields}
        
        # 7. Apply exclude_fields filter
        for field in exclude_fields:
            result.pop(field, None)
        
        # 8. Add constant fields
        for field, value in add_fields.items():
            result[field] = value
        
        # 9. Apply nested grouping
        if nested_group:
            prefix = nested_group.get("prefix", "meta")
            fields_to_group = nested_group.get("fields", [])
            nested_obj = {}
            
            for field in fields_to_group:
                if field in result:
                    nested_obj[field] = result.pop(field)
            
            if nested_obj:
                result[prefix] = nested_obj
        
        # 10. Remove empty values if requested
        if remove_empty:
            result = {k: v for k, v in result.items() if v is not None and v != ""}
        
        return result
    
    def _get_nested_value(self, obj: Dict[str, Any], path: str) -> Any:
        """Get value from nested path like 'metadata.width'."""
        keys = path.split('.')
        value = obj
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def _set_nested_value(self, obj: Dict[str, Any], path: str, value: Any):
        """Set value at nested path like 'metadata.width'."""
        keys = path.split('.')
        current = obj
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    async def transform_file(
        self,
        input_path: Path,
        output_path: Path,
        mapping: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Transform a JSON/JSONL file based on mapping.
        
        Returns:
            Statistics about transformation
        """
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        ext = input_path.suffix.lower()
        
        # Read input
        if ext == '.jsonl':
            data = []
            with open(input_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        data.append(json.loads(line))
        else:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        # Transform
        if isinstance(data, list):
            transformed = [self._transform_object(item, mapping, options or {}) for item in data]
        else:
            transformed = self._transform_object(data, mapping, options or {})
        
        # Write output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        out_ext = output_path.suffix.lower()
        if out_ext == '.jsonl':
            with open(output_path, 'w', encoding='utf-8') as f:
                for item in (transformed if isinstance(transformed, list) else [transformed]):
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
        else:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(transformed, f, ensure_ascii=False, indent=2)
        
        return {
            "input_file": str(input_path),
            "output_file": str(output_path),
            "input_count": len(data) if isinstance(data, list) else 1,
            "output_count": len(transformed) if isinstance(transformed, list) else 1,
        }
    
    def infer_mapping_from_samples(
        self,
        source_sample: Dict[str, Any],
        target_sample: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Infer field mapping from source and target samples.
        
        Useful for creating mapping when you have example data.
        """
        mapping = {"field_mappings": {}}
        
        # Try to match fields by similar names or values
        for src_key, src_val in source_sample.items():
            # Exact match
            if src_key in target_sample:
                mapping["field_mappings"][src_key] = src_key
                continue
            
            # Try common variations
            variations = [
                src_key.lower(),
                src_key.replace("_", ""),
                src_key.replace("-", "_"),
                src_key.replace(" ", "_"),
            ]
            
            for var in variations:
                for tgt_key in target_sample.keys():
                    if var == tgt_key.lower() or var == tgt_key.replace("_", "").lower():
                        mapping["field_mappings"][src_key] = tgt_key
                        break
        
        return mapping
    
    def validate_mapping(self, mapping: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a mapping configuration."""
        errors = []
        warnings = []
        
        if "field_mappings" in mapping:
            for src, tgt in mapping["field_mappings"].items():
                if not isinstance(src, str) or not isinstance(tgt, str):
                    errors.append(f"Field mapping keys and values must be strings: {src} -> {tgt}")
        
        if "value_transforms" in mapping:
            for field, transform in mapping["value_transforms"].items():
                if "type" not in transform:
                    errors.append(f"Value transform for '{field}' missing 'type'")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }


# Singleton
schema_mapping_service = SchemaMappingService()
