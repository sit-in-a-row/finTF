import pandas as pd

def get_R_m_minus_R_f(market_df, bond_df):
    market_df.index = pd.to_datetime(market_df.index)
    bond_df.index = pd.to_datetime(bond_df.index)

    merged_df = pd.merge(market_df, bond_df, left_index=True, right_index=True)
    merged_df['R_m - R_f'] = merged_df['Return_x'] - (merged_df['Bond_Yield']/100)

    merged_df = merged_df['R_m - R_f']

    return merged_df