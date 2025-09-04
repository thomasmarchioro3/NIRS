"""
Copyright (C) 2025, CEA

This program is free software; you can redistribute it and/or modify
it under the terms of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0
International License.

You should have received a copy of the license along with this
program. If not, see <https://creativecommons.org/licenses/by-nc-sa/4.0/>.
"""

import pandas as pd
from sklearn.preprocessing import StandardScaler, OrdinalEncoder

from typing import Optional

class NIDS_Preprocessor:
    """
    Preprocessor class for NIDS datasets.

    Args:
        cat_cols (list[str], optional): List of categorical column names. If None, all
            columns are treated as numerical, and the categorical columns
            are inferred from the data as the columns with non-numerical
            values. Defaults to None.
    """


    def __init__(self, cat_cols: Optional[list[str]]=None):

        self.scaler = StandardScaler()
        self.encoder = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)

        self.cat_cols = cat_cols
        self.is_fitted = False


    def fit(self, X: pd.DataFrame):
        """
        Fits the preprocessor to the input data.

        Args:
            X (pd.DataFrame): Input data to fit the preprocessor.

        Returns:
            None
        """
        X = X.copy()
        
        if self.cat_cols is None:
            self.cat_cols = self.get_cat_cols(X)

        X.loc[:, self.cat_cols] = self.encoder.fit_transform(X[self.cat_cols])
        self.scaler.fit(X)
        self.is_fitted = True
    
    def transform(self, X: pd.DataFrame):
        """
        Transforms the input data using the fitted preprocessor.

        Args:
            X (pd.DataFrame): Input data to transform.

        Returns:
            pd.DataFrame: Transformed data.

        Raises:
            ValueError: If the preprocessor is not fitted.
        """
        if not self.is_fitted:
            raise ValueError('Preprocessor is not fitted')

        X = X.copy()
        X.loc[:, self.cat_cols] = self.encoder.transform(X[self.cat_cols])
        X = pd.DataFrame(self.scaler.transform(X), columns=X.columns, index=X.index)
        return X
    
    def fit_transform(self, X: pd.DataFrame):
        """
        Fits the preprocessor to the input data and transforms it.
        More memory-efficient than calling fit() followed by transform().

        Args:
            X (pd.DataFrame): Input data to fit and transform.

        Returns:
            pd.DataFrame: Transformed data.

        """
        X = X.copy()
        
        if self.cat_cols is None:
            self.cat_cols = self.get_cat_cols(X)

        X.loc[:, self.cat_cols] = self.encoder.fit_transform(X[self.cat_cols])
        X = pd.DataFrame(self.scaler.fit_transform(X), columns=X.columns, index=X.index)
        self.is_fitted = True
        return X

    @staticmethod
    def get_cat_cols(X: pd.DataFrame) -> list:
        num_cols = X.select_dtypes('number').columns.tolist()
        cat_cols = list(set(X.columns) - set(num_cols))
        return cat_cols
    
