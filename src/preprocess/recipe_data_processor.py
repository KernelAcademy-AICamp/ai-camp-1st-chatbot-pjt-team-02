import pandas as pd
import re

def clean_and_split_ingredients(text: str):
    """
    Cleans and splits a string of ingredients into a list of individual ingredients.
    Handles removal of specific patterns, control characters, and extra spaces.
    """
    if not isinstance(text, str):
        return []
    
    # 1️⃣ "[재료]" 또는 "[...]" 전체 제거
    text = re.sub(r'\[[^\]]*\]', '', text)
    
    # 2️⃣ 제어문자, 유니코드 공백 제거
    text = re.sub(r'[\x00-\x1F\u200b\xa0]+', '', text)
    
    # 3️⃣ 앞뒤 불필요한 공백 제거
    text = text.strip()
    
    # 4️⃣ '|' 기준 분리 후, 각각 공백 정리
    ingredients = [i.strip() for i in text.split('|') if i.strip()]
    
    return ingredients

def process_recipe_data(file_paths: list) -> pd.DataFrame:
    """
    Reads and processes multiple recipe CSV files, cleans the ingredient data,
    and returns a concatenated DataFrame.

    Args:
        file_paths: A list of absolute paths to the raw recipe CSV files.

    Returns:
        A cleaned pandas DataFrame containing recipe names and processed ingredients.
    """
    all_recipe_dfs = []
    for file_path in file_paths:
        try:
            # Attempt to read with default UTF-8, then euc-kr, then CP949
            df = pd.read_csv(file_path)
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(file_path, encoding='euc-kr', encoding_errors='ignore')
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding='CP949', encoding_errors='ignore')
        all_recipe_dfs.append(df)

    recipe_df = pd.concat(all_recipe_dfs)

    use_column_list_recipe = ['CKG_NM', 'CKG_MTRL_CN']
    recipe_df = recipe_df[use_column_list_recipe]
    recipe_df.dropna(inplace=True)
    recipe_df.columns = ['요리명', '재료']
    recipe_df.reset_index(drop=True, inplace=True)
    recipe_df['재료'] = recipe_df['재료'].apply(clean_and_split_ingredients)
    
    return recipe_df

if __name__ == '__main__':
    # Example usage (assuming the raw data files exist)
    # This part will only run when the script is executed directly
    # For actual use, you would call process_recipe_data from another script
    file_paths = [
        '../../data/raw/TB_RECIPE_SEARCH_241226.csv',
        '../../data/raw/TB_RECIPE_SEARCH-220701.csv',
        '../../data/raw/TB_RECIPE_SEARCH-20231130.csv'
    ] # Adjust paths as necessary
    cleaned_recipe_df = process_recipe_data(file_paths)
    print(cleaned_recipe_df.head())
    cleaned_recipe_df.sample(100).to_csv('../../data/preprocess/recipe_sample_df.csv', index=False)
    cleaned_recipe_df.to_csv('../../data/preprocess/recipe_df.csv', index=False)
