import pandas as pd

def get_R_i_minus_R_f(stock_df, bond_df):
    stock_df.index = pd.to_datetime(stock_df.index)
    bond_df.index = pd.to_datetime(bond_df.index)

    merged_df = pd.merge(stock_df, bond_df, left_index=True, right_index=True)
    merged_df['R_i - R_f'] = merged_df['Return_x'] - (merged_df['Bond_Yield']/100)

    merged_df = merged_df['R_i - R_f']

    return merged_df