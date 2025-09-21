def display_dataframe_to_user(name: str, dataframe):
    print(f"=== {name} ===")
    print(dataframe.head(20))
