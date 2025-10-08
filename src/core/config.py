# functools is a module which has tools for working with functions and callable objects
# lru cache is Least Recently Used cache which is cache replacement policy.
# a cache replacement policy are optimizing instructions that aid in managing cache effectively.
# caching improves performance by keeping recent data items in memory locations that are computationally cheaper to accesss.
from functools import lru_cache

# pydantic module helps define request and response models
# It validates the incoming JSON files so that I need not write too many "if" checks
from pydantic import BaseModel

# os - miscellanous operating system interfaces
# os provides a protable way for python programs to interact with the operating system (irrespective of the type)
import os

# ⬇️ add these two lines
from dotenv import load_dotenv
load_dotenv()  # loads .env from project root into process env

# define the basemodel in pydantic
# Settings here is a model with 4 fields:
# sqlite path which is a string and is not required as it has a default value of data/retail.db
# the rest three are similar strings with the only difference of an OR operating allowing any str or None to not raise a flag
# they also have the default values set to the specific list or str when not present or retrived are None.
# Got a warning when used model_provider and model_name as pydantic uses model_ prefix for its own internals. So changed to llm_.
class Settings(BaseModel):
    # DB
    sqlite_path: str = "data/retail.db"

    # LLM provider + model (use llm_* to avoid Pydantic 'model_' namespace warning)
    llm_provider: str | None = os.getenv("MODEL_PROVIDER")          # e.g., "openai"
    llm_model: str | None = os.getenv("MODEL_NAME")                 # e.g., "gpt-4o-mini"

    # Secrets / flags
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    use_llm: bool = os.getenv("USE_LLM", "false").strip().lower() == "true"
    
# using caching to get the settings optimally
@lru_cache
def get_settings() -> Settings:
    return Settings()

# Python can run the file in two ways: as a script (python x.py) or as a imported module
# so this of statement ensures that we only run the following if the file is executed directly but not when it is imported elsewhere.
# the logic stems from from the fact that Python sets a special inbuilt variable to _name_ to "_main_" if the file is run directly
# for the imported module case it will be of the form: src.core.config
# once the file is run then the settings are retrived and then printed.

if __name__ == "__main__":
    s = get_settings()
    print("Settings loaded:",
          {"sqlite_path": s.sqlite_path,
           "llm_provider": s.llm_provider,
           "llm_model": s.llm_model,
           "use_llm": s.use_llm,
           "openai_api_key_set": bool(s.openai_api_key)})


