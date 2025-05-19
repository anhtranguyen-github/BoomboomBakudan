# File: bitcoin_trading/models/model_factory.py
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from xgboost import XGBClassifier
from catboost import CatBoostClassifier

class ModelFactory:
    """Factory class for creating ML models."""
    
    @staticmethod
    def create_models(n_estimators=25):
        """Create a list of model tuples (name, model)."""
        models = []
        
        # Lightweight models
        models.append(('LDA', LinearDiscriminantAnalysis()))
        models.append(('KNN', KNeighborsClassifier()))
        models.append(('TREE', DecisionTreeClassifier()))
        models.append(('NB', GaussianNB()))
        
        # More advanced models
        models.append(('GBM', GradientBoostingClassifier(n_estimators=n_estimators)))
        models.append(('XGB', XGBClassifier(n_estimators=n_estimators, eval_metric='logloss')))
        models.append(('CAT', CatBoostClassifier(silent=True, n_estimators=n_estimators)))
        models.append(('RF', RandomForestClassifier(n_estimators=n_estimators)))
        
        return models