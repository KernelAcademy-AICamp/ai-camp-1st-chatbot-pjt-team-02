import pandas as pd

def process_food_database(file_path: str) -> pd.DataFrame:
    """
    Processes the raw food database Excel file to extract and clean relevant nutritional data.

    Args:
        file_path: The absolute path to the raw Excel file (e.g., './data/raw/국가표준식품성분표_250426공개.xlsx').

    Returns:
        A cleaned pandas DataFrame containing selected food nutritional information.
    """
    food_database_sheet = '국가표준식품성분 Database 10.2'
    food_database_df = pd.read_excel(file_path, sheet_name=food_database_sheet, header=1)

    use_column_list_food = [
        '식품군', '식품명', '출처', '에너지', '단백질', '인', '칼륨', '나트륨'
    ]

    food_database_cleaned_df = food_database_df[use_column_list_food].copy()
    food_database_cleaned_df = food_database_cleaned_df.loc[1:]
    food_database_cleaned_df['영양성분함량기준량'] = '100g'
    food_database_cleaned_df['단백질(mg)'] = food_database_cleaned_df['단백질'] * 100
    food_database_cleaned_df = food_database_cleaned_df.drop('단백질', axis=1)

    food_database_cleaned_df['식품명'] = food_database_cleaned_df['식품명'].apply(lambda x: '_'.join(x.split(', ')))
    food_database_cleaned_df = food_database_cleaned_df[['식품군', '식품명', '출처', '에너지', '단백질(mg)', '인', '칼륨', '나트륨', '영양성분함량기준량']]

    food_database_cleaned_df.columns = ['식품군', '식품명', '출처', '에너지(kcal)', '단백질(mg)', '인(mg)', '칼륨(mg)', '나트륨(mg)', '영양성분함량기준량']
    food_database_cleaned_df.reset_index(drop=True, inplace=True)
    
    return food_database_cleaned_df

if __name__ == '__main__':
    # Example usage (assuming the raw data file exists)
    # This part will only run when the script is executed directly
    # For actual use, you would call process_food_database from another script
    file_path = '../../data/raw/국가표준식품성분표_250426공개.xlsx' # Adjust path as necessary
    cleaned_df = process_food_database(file_path)
    print(cleaned_df.head())
    cleaned_df.to_csv('../../data/preprocess/food_database_cleaned_df.csv', index=False)
