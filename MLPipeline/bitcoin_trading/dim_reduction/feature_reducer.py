# File: bitcoin_trading/dim_reduction/feature_reducer.py
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler, MinMaxScaler, Normalizer, RobustScaler
from sklearn.decomposition import PCA, SparsePCA, KernelPCA, IncrementalPCA, TruncatedSVD, FastICA
from sklearn.random_projection import GaussianRandomProjection, SparseRandomProjection

class FeatureReducer:
    """Class for dimensionality reduction."""
    
    def __init__(self, method='fastica', n_components=5, random_state=42):
        self.method = method
        self.n_components = n_components
        self.random_state = random_state
        self.model = self._create_model()
        
    def _create_model(self):
        """Create the dimensionality reduction model."""
        if self.method == 'pca':
            return PCA(n_components=self.n_components, random_state=self.random_state)
        elif self.method == 'sparsepca':
            return SparsePCA(n_components=self.n_components, random_state=self.random_state)
        elif self.method == 'kernelpca':
            return KernelPCA(n_components=self.n_components, random_state=self.random_state)
        elif self.method == 'incrementalpca':
            return IncrementalPCA(n_components=self.n_components)
        elif self.method == 'truncatedsvd':
            return TruncatedSVD(n_components=self.n_components, random_state=self.random_state)
        elif self.method == 'fastica':
            return FastICA(n_components=self.n_components, random_state=self.random_state)
        elif self.method == 'gaussianrandomprojection':
            return GaussianRandomProjection(n_components=self.n_components, random_state=self.random_state)
        elif self.method == 'sparserandomprojection':
            return SparseRandomProjection(n_components=self.n_components, random_state=self.random_state)
        else:
            raise ValueError(f"Unknown method: {self.method}")
    
    def reduce_features(self, df, target_col='signal', scaler=None, plot=True):
        """Reduce features and return a new dataframe."""
        # Extract features and target
        X = df.drop(columns=[target_col])
        y = df[target_col]
        
        # Scale features if requested
        if scaler:
            if isinstance(scaler, str):
                if scaler == 'standard':
                    scaler = StandardScaler()
                elif scaler == 'minmax':
                    scaler = MinMaxScaler()
                elif scaler == 'robust':
                    scaler = RobustScaler()
                elif scaler == 'normalizer':
                    scaler = Normalizer()
                else:
                    raise ValueError(f"Unknown scaler: {scaler}")
            
            X_scaled = pd.DataFrame(
                scaler.fit_transform(X),
                index=X.index,
                columns=X.columns
            )
            X_to_reduce = X_scaled
        else:
            X_to_reduce = X
        
        # Reduce features
        X_reduced = self.model.fit_transform(X_to_reduce)
        X_reduced_df = pd.DataFrame(
            X_reduced,
            index=X.index,
            columns=[f'component_{i}' for i in range(self.n_components)]
        )
        
        # Plot if requested
        if plot:
            self.plot_result(X_reduced_df, y)
        
        # Add target back
        X_reduced_df[target_col] = y
        
        return X_reduced_df
    
    def plot_result(self, X_reduced_df, y):
        """Plot the reduced features."""
        sns.set_style('whitegrid')
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Create plot data
        plot_df = pd.DataFrame({
            'Component 1': X_reduced_df.iloc[:, 0],
            'Component 2': X_reduced_df.iloc[:, 1] if self.n_components > 1 else np.zeros(len(X_reduced_df)),
            'Label': y
        })
        
        # Create scatter plot
        sns.scatterplot(
            x='Component 1',
            y='Component 2',
            hue='Label',
            data=plot_df,
            linewidth=0.5,
            alpha=0.5,
            s=15,
            edgecolor='k',
            ax=ax
        )
        
        # Style the plot
        ax.set_title(f'{self.method} Dimensionality Reduction')
        for i in ['top', 'right', 'bottom', 'left']:
            ax.spines[i].set_color('black')
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.grid(axis='both', ls='--', alpha=0.9)
        
        plt.legend()
        plt.tight_layout()
        plt.show()