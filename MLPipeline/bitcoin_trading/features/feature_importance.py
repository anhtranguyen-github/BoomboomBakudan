# File: bitcoin_trading/features/feature_importance.py
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import shap
from sklearn.preprocessing import MinMaxScaler
from sklearn.feature_selection import SelectKBest, f_regression
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from catboost import CatBoostRegressor

class FeatureImportanceAnalyzer:
    """Analyze feature importance using multiple methods."""
    
    def __init__(self, df, target_col='signal', n_estimators=25):
        self.df = df.copy()
        self.target_col = target_col
        self.n_estimators = n_estimators
        
    def analyze(self):
        """Run all feature importance methods and return combined results."""
        # Prepare data
        y = self.df[self.target_col]
        X = self.df.drop(columns=[self.target_col])
        
        # Get importance scores from different methods
        corr_scores = self._correlation_importance()
        shap_scores = self._shap_importance(X, y)
        catboost_scores = self._catboost_importance(X, y)
        rf_scores = self._randomforest_importance(X, y)
        xgb_scores = self._xgboost_importance(X, y)
        kbest_scores = self._kbest_importance(X, y)
        
        # Combine scores
        combined_df = pd.concat([
            corr_scores,
            shap_scores,
            catboost_scores,
            rf_scores,
            xgb_scores,
            kbest_scores
        ], axis=1)
        
        # Scale scores
        scaler = MinMaxScaler()
        scaled_values = scaler.fit_transform(combined_df.values)
        scaled_df = pd.DataFrame(
            scaled_values,
            index=combined_df.index,
            columns=combined_df.columns
        )
        
        return scaled_df
    
    def _correlation_importance(self):
        """Get feature importance from correlation with target."""
        corr_matrix = self.df.corr().transpose()
        corr = corr_matrix.loc[:, self.df.columns == self.target_col].transpose().copy()
        del corr[self.target_col]
        return pd.Series(np.abs(corr.iloc[0]), name='CORR')
    
    def _shap_importance(self, X, y):
        """Get feature importance from SHAP values."""
        model = CatBoostRegressor(silent=True, n_estimators=self.n_estimators)
        model.fit(X, y)
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)
        shap_sum = np.abs(shap_values).mean(axis=0)
        return pd.Series(shap_sum, index=X.columns, name='SHAP')
    
    def _catboost_importance(self, X, y):
        """Get feature importance from CatBoost."""
        model = CatBoostRegressor(silent=True, n_estimators=self.n_estimators)
        model.fit(X, y)
        return pd.Series(model.feature_importances_, index=X.columns, name='CAT')
    
    def _randomforest_importance(self, X, y):
        """Get feature importance from Random Forest."""
        model = RandomForestRegressor(n_estimators=self.n_estimators, random_state=0, n_jobs=-1)
        model.fit(X, y)
        return pd.Series(model.feature_importances_, index=X.columns, name='RF')
    
    def _xgboost_importance(self, X, y):
        """Get feature importance from XGBoost."""
        model = XGBRegressor(n_estimators=self.n_estimators, learning_rate=0.5, verbosity=0)
        model.fit(X, y)
        return pd.Series(model.feature_importances_, index=X.columns, name='XGB')
    
    def _kbest_importance(self, X, y):
        """Get feature importance from SelectKBest."""
        model = SelectKBest(k=5, score_func=f_regression)
        model.fit(X, y)
        return pd.Series(model.scores_, index=X.columns, name='KBEST')
    
    def plot_importance(self, scaled_df=None):
        """Plot feature importance."""
        if scaled_df is None:
            scaled_df = self.analyze()
        
        # Plotly bar chart
        fig = px.bar(
            scaled_df.T,
            barmode='group',
            title='Scaled Feature Importance',
            labels={'value': 'Importance', 'variable': 'Feature'},
            height=500
        )
        
        fig.update_layout(
            template='plotly_white',
            font=dict(family='sans-serif', size=12),
            margin=dict(l=60, r=40, t=50, b=40)
        )
        
        fig.update_traces(width=0.25)
        fig.show()