"""
Auto Database Setup Service
Automatically configures databases for generated applications
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class DatabaseAutoSetup:
    """Automatically setup databases for applications"""
    
    def __init__(self):
        self.supported_databases = ["mongodb", "postgresql", "mysql", "sqlite"]
    
    async def analyze_data_requirements(
        self,
        prompt: str,
        files: List[Dict]
    ) -> Dict:
        """
        Analyze application to determine database needs
        
        Returns schema and configuration recommendations
        """
        try:
            # Detect data entities from prompt and code
            entities = self._extract_entities(prompt, files)
            
            # Generate schema
            schema = self._generate_schema(entities)
            
            # Recommend database type
            db_recommendation = self._recommend_database(entities, prompt)
            
            return {
                "success": True,
                "entities": entities,
                "schema": schema,
                "recommended_database": db_recommendation,
                "setup_code": self._generate_setup_code(schema, db_recommendation)
            }
            
        except Exception as e:
            logger.error(f"Database analysis failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _extract_entities(self, prompt: str, files: List[Dict]) -> List[Dict]:
        """Extract data entities from prompt and code"""
        entities = []
        
        # Common entity patterns
        entity_keywords = [
            "user", "product", "order", "customer", "post", "comment",
            "article", "blog", "image", "video", "category", "tag",
            "invoice", "payment", "subscription", "review", "rating"
        ]
        
        prompt_lower = prompt.lower()
        
        for keyword in entity_keywords:
            if keyword in prompt_lower:
                # Extract entity with basic fields
                entity = {
                    "name": keyword.capitalize(),
                    "fields": self._infer_fields_for_entity(keyword, prompt_lower)
                }
                entities.append(entity)
        
        # Analyze code for model definitions
        for file in files:
            if file.get("path", "").endswith(".py"):
                content = file.get("content", "")
                if "class " in content and "BaseModel" in content:
                    # Parse Pydantic models
                    code_entities = self._parse_pydantic_models(content)
                    entities.extend(code_entities)
        
        # Remove duplicates
        unique_entities = {}
        for entity in entities:
            name = entity["name"]
            if name not in unique_entities:
                unique_entities[name] = entity
            else:
                # Merge fields
                existing_fields = {f["name"] for f in unique_entities[name]["fields"]}
                for field in entity["fields"]:
                    if field["name"] not in existing_fields:
                        unique_entities[name]["fields"].append(field)
        
        return list(unique_entities.values())
    
    def _infer_fields_for_entity(self, entity_name: str, prompt: str) -> List[Dict]:
        """Infer fields for an entity based on context"""
        common_fields = {
            "user": [
                {"name": "id", "type": "string", "required": True, "primary_key": True},
                {"name": "email", "type": "string", "required": True, "unique": True},
                {"name": "name", "type": "string", "required": True},
                {"name": "password_hash", "type": "string", "required": True},
                {"name": "created_at", "type": "datetime", "required": True},
            ],
            "product": [
                {"name": "id", "type": "string", "required": True, "primary_key": True},
                {"name": "name", "type": "string", "required": True},
                {"name": "description", "type": "text", "required": False},
                {"name": "price", "type": "float", "required": True},
                {"name": "image_url", "type": "string", "required": False},
                {"name": "created_at", "type": "datetime", "required": True},
            ],
            "post": [
                {"name": "id", "type": "string", "required": True, "primary_key": True},
                {"name": "title", "type": "string", "required": True},
                {"name": "content", "type": "text", "required": True},
                {"name": "author_id", "type": "string", "required": True, "foreign_key": "user.id"},
                {"name": "created_at", "type": "datetime", "required": True},
            ],
            "order": [
                {"name": "id", "type": "string", "required": True, "primary_key": True},
                {"name": "user_id", "type": "string", "required": True, "foreign_key": "user.id"},
                {"name": "total", "type": "float", "required": True},
                {"name": "status", "type": "string", "required": True},
                {"name": "created_at", "type": "datetime", "required": True},
            ]
        }
        
        return common_fields.get(entity_name, [
            {"name": "id", "type": "string", "required": True, "primary_key": True},
            {"name": "name", "type": "string", "required": True},
            {"name": "created_at", "type": "datetime", "required": True},
        ])
    
    def _parse_pydantic_models(self, code: str) -> List[Dict]:
        """Parse Pydantic models from Python code"""
        import re
        
        entities = []
        
        # Find class definitions
        class_pattern = r"class\s+(\w+)\(BaseModel\):(.*?)(?=class\s+\w+|$)"
        matches = re.finditer(class_pattern, code, re.DOTALL)
        
        for match in matches:
            class_name = match.group(1)
            class_body = match.group(2)
            
            # Extract fields
            field_pattern = r"(\w+):\s*([\w\[\]]+)"
            field_matches = re.finditer(field_pattern, class_body)
            
            fields = []
            for field_match in field_matches:
                field_name = field_match.group(1)
                field_type = field_match.group(2)
                
                # Convert Python type to database type
                db_type = self._python_type_to_db_type(field_type)
                
                fields.append({
                    "name": field_name,
                    "type": db_type,
                    "required": "Optional" not in field_type
                })
            
            if fields:
                entities.append({
                    "name": class_name,
                    "fields": fields
                })
        
        return entities
    
    def _python_type_to_db_type(self, python_type: str) -> str:
        """Convert Python type hints to database types"""
        type_mapping = {
            "str": "string",
            "int": "integer",
            "float": "float",
            "bool": "boolean",
            "datetime": "datetime",
            "List": "array",
            "Dict": "json",
            "Optional": "string"
        }
        
        for py_type, db_type in type_mapping.items():
            if py_type in python_type:
                return db_type
        
        return "string"
    
    def _generate_schema(self, entities: List[Dict]) -> Dict:
        """Generate database schema from entities"""
        schema = {
            "tables": [],
            "relationships": []
        }
        
        for entity in entities:
            table = {
                "name": entity["name"].lower() + "s",
                "fields": entity["fields"],
                "indexes": []
            }
            
            # Add indexes for foreign keys
            for field in entity["fields"]:
                if field.get("foreign_key"):
                    table["indexes"].append({
                        "name": f"idx_{table['name']}_{field['name']}",
                        "fields": [field["name"]]
                    })
                    
                    # Add relationship
                    schema["relationships"].append({
                        "from_table": table["name"],
                        "from_field": field["name"],
                        "to_table": field["foreign_key"].split(".")[0] + "s",
                        "to_field": field["foreign_key"].split(".")[1],
                        "type": "many-to-one"
                    })
            
            schema["tables"].append(table)
        
        return schema
    
    def _recommend_database(self, entities: List[Dict], prompt: str) -> str:
        """Recommend database type based on requirements"""
        prompt_lower = prompt.lower()
        
        # Check for specific database mentions
        if "postgres" in prompt_lower or "postgresql" in prompt_lower:
            return "postgresql"
        elif "mysql" in prompt_lower:
            return "mysql"
        elif "mongodb" in prompt_lower or "mongo" in prompt_lower:
            return "mongodb"
        elif "sqlite" in prompt_lower:
            return "sqlite"
        
        # Make recommendation based on characteristics
        total_entities = len(entities)
        has_complex_relations = any(
            any(f.get("foreign_key") for f in e["fields"])
            for e in entities
        )
        
        if has_complex_relations and total_entities > 3:
            return "postgresql"  # Best for complex relational data
        elif "flexible" in prompt_lower or "schema" in prompt_lower:
            return "mongodb"  # Best for flexible schema
        else:
            return "mongodb"  # Default - easy to use
    
    def _generate_setup_code(self, schema: Dict, db_type: str) -> Dict:
        """Generate database setup code"""
        if db_type == "mongodb":
            return self._generate_mongodb_code(schema)
        elif db_type == "postgresql":
            return self._generate_postgresql_code(schema)
        else:
            return self._generate_mongodb_code(schema)  # Fallback
    
    def _generate_mongodb_code(self, schema: Dict) -> Dict:
        """Generate MongoDB setup code"""
        models_code = """
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os

# MongoDB connection
mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
client = AsyncIOMotorClient(mongo_url)
db = client[os.getenv("DB_NAME", "app_database")]

# Collections
"""
        
        for table in schema["tables"]:
            collection_name = table["name"]
            models_code += f"{collection_name}_collection = db.{collection_name}\n"
        
        models_code += "\n# Pydantic models\n"
        
        for table in schema["tables"]:
            class_name = table["name"].rstrip('s').capitalize()
            models_code += f"\nclass {class_name}(BaseModel):\n"
            
            for field in table["fields"]:
                field_type = field["type"]
                py_type = self._db_type_to_python(field_type)
                optional = "" if field.get("required") else "Optional[...]"
                
                if optional:
                    models_code += f"    {field['name']}: Optional[{py_type}] = None\n"
                else:
                    models_code += f"    {field['name']}: {py_type}\n"
        
        return {
            "backend": {
                "models.py": models_code
            },
            "setup_instructions": """
# MongoDB Setup

1. Install MongoDB locally or use MongoDB Atlas
2. Set environment variables:
   - MONGO_URL=mongodb://localhost:27017 (or your MongoDB connection string)
   - DB_NAME=your_database_name

3. Collections will be created automatically on first insert
"""
        }
    
    def _generate_postgresql_code(self, schema: Dict) -> Dict:
        """Generate PostgreSQL setup code"""
        sql_code = "-- Database Schema\n\n"
        
        for table in schema["tables"]:
            sql_code += f"CREATE TABLE {table['name']} (\n"
            
            for i, field in enumerate(table["fields"]):
                sql_type = self._db_type_to_sql(field["type"])
                constraints = []
                
                if field.get("primary_key"):
                    constraints.append("PRIMARY KEY")
                if field.get("required") and not field.get("primary_key"):
                    constraints.append("NOT NULL")
                if field.get("unique"):
                    constraints.append("UNIQUE")
                
                constraint_str = " " + " ".join(constraints) if constraints else ""
                comma = "," if i < len(table["fields"]) - 1 else ""
                
                sql_code += f"    {field['name']} {sql_type}{constraint_str}{comma}\n"
            
            sql_code += ");\n\n"
        
        # Add foreign keys
        for rel in schema.get("relationships", []):
            sql_code += f"ALTER TABLE {rel['from_table']} ADD CONSTRAINT fk_{rel['from_table']}_{rel['from_field']} "
            sql_code += f"FOREIGN KEY ({rel['from_field']}) REFERENCES {rel['to_table']}({rel['to_field']});\n"
        
        sql_code += "\n-- Indexes\n"
        for table in schema["tables"]:
            for index in table.get("indexes", []):
                fields = ", ".join(index["fields"])
                sql_code += f"CREATE INDEX {index['name']} ON {table['name']} ({fields});\n"
        
        return {
            "backend": {
                "schema.sql": sql_code
            },
            "setup_instructions": """
# PostgreSQL Setup

1. Install PostgreSQL
2. Create database: createdb your_database_name
3. Run schema: psql your_database_name < schema.sql
4. Set environment variable: DATABASE_URL=postgresql://user:pass@localhost/dbname
"""
        }
    
    def _db_type_to_python(self, db_type: str) -> str:
        """Convert database type to Python type"""
        mapping = {
            "string": "str",
            "integer": "int",
            "float": "float",
            "boolean": "bool",
            "datetime": "datetime",
            "array": "List",
            "json": "Dict",
            "text": "str"
        }
        return mapping.get(db_type, "str")
    
    def _db_type_to_sql(self, db_type: str) -> str:
        """Convert database type to SQL type"""
        mapping = {
            "string": "VARCHAR(255)",
            "integer": "INTEGER",
            "float": "DECIMAL(10,2)",
            "boolean": "BOOLEAN",
            "datetime": "TIMESTAMP",
            "array": "JSON",
            "json": "JSON",
            "text": "TEXT"
        }
        return mapping.get(db_type, "VARCHAR(255)")
