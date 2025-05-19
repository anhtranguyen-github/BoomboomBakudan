from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.feature_selection import SelectKBest, f_regression
from sklearn.decomposition import PCA

class ModelPipeline:
    """Class for creating model pipelines with different preprocessing strategies."""
    
    @staticmethod
    def create_pipeline(model, preprocess_strategy='standard', feature_select=None, n_components=None):
        """
        Create a pipeline with preprocessing steps and a model.
        
        Parameters:
        -----------
        model : estimator
            The model to train
        preprocess_strategy : str
            Strategy for preprocessing: 'none', 'standard', 'minmax', 'robust', 'impute'
        feature_select : str or None
            Strategy for feature selection: None, 'kbest', 'pca'
        n_components : int or None
            Number of components for feature selection
        
        Returns:
        --------
        Pipeline
            A scikit-learn pipeline with preprocessing steps and the model
        """
        steps = []
        
        # Add preprocessing step based on strategy
        if preprocess_strategy == 'standard':
            steps.append(('scaler', StandardScaler()))
        elif preprocess_strategy == 'minmax':
            steps.append(('scaler', MinMaxScaler()))
        elif preprocess_strategy == 'robust':
            steps.append(('scaler', RobustScaler()))
        elif preprocess_strategy == 'impute':
            steps.append(('imputer', SimpleImputer(strategy='mean')))
            steps.append(('scaler', StandardScaler()))
        
        # Add feature selection if specified
        if feature_select == 'kbest' and n_components:
            steps.append(('select', SelectKBest(score_func=f_regression, k=n_components)))
        elif feature_select == 'pca' and n_components:
            steps.append(('pca', PCA(n_components=n_components)))
        
        # Add the model as the final step
        steps.append(('model', model))
        
        return Pipeline(steps)
        
    @staticmethod
    def get_pipeline_strategies():
        """Get a list of available pipeline strategies for experimentation."""
        preprocess_strategies = ['none', 'standard', 'minmax', 'robust', 'impute']
        feature_select_strategies = [None, 'kbest', 'pca']
        
        return {
            'preprocess': preprocess_strategies,
            'feature_select': feature_select_strategies
        } 