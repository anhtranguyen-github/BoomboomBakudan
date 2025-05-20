# File: bitcoin_trading/models/model_evaluator.py
import numpy as np
import pandas as pd
import time
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import KFold, cross_val_score, train_test_split
from sklearn.metrics import accuracy_score

class ModelEvaluator:
    """Class for evaluating machine learning models."""
    
    def __init__(self, models, n_fold=5, scoring='accuracy'):
        self.models = models
        self.n_fold = n_fold
        self.scoring = scoring
        
    def evaluate(self, df, target_col='signal', test_size=0.2, plot=True):
        """Evaluate models using cross-validation and train/test split."""
        
        # Split data
        train_df, eval_df = train_test_split(df, test_size=test_size, shuffle=False)
        
        # Prepare features and target
        y_train = train_df[target_col]
        X_train = train_df.drop(columns=[target_col])
        y_eval = eval_df[target_col]
        X_eval = eval_df.drop(columns=[target_col])
        X_all = pd.concat([X_train, X_eval], axis=0)
        y_all = pd.concat([y_train, y_eval], axis=0)
        
        print(f'Using features: {X_train.columns.tolist()}')
        print(f'Target variable: {target_col}\n')
        
        # Evaluate models
        cv_results = []
        names = []
        train_scores = []
        eval_scores = []
        all_scores = []
        cv_times = []
        train_test_times = []
        all_times = []
        
        for name, model in self.models:
            names.append(name)
            
            # Track training process for each model
            print(f"\nTraining model: {name}")
            model_start_time = time.time()
            
            # Cross validation
            t0 = time.time()
            kfold = KFold(n_splits=self.n_fold)
            cv_score = cross_val_score(model, X_train, y_train, cv=kfold, scoring=self.scoring)
            t1 = time.time()
            cv_results.append(cv_score)
            cv_time = t1 - t0
            cv_times.append(cv_time)
            
            # Train and eval
            t2 = time.time()
            model_fit = model.fit(X_train, y_train)
            train_score = accuracy_score(model_fit.predict(X_train), y_train)
            train_scores.append(train_score)
            eval_score = accuracy_score(model_fit.predict(X_eval), y_eval)
            eval_scores.append(eval_score)
            t3 = time.time()
            train_test_time = t3 - t2
            train_test_times.append(train_test_time)
            
            # All data
            t4 = time.time()
            model_fit = model.fit(X_all, y_all)
            all_score = accuracy_score(model_fit.predict(X_all), y_all)
            all_scores.append(all_score)
            t5 = time.time()
            all_time = t5 - t4
            all_times.append(all_time)
            
            # Record and print model training time
            model_training_time = time.time() - model_start_time
            print(f"Model {name} training time: {model_training_time:.2f} seconds")
            
            print(f"{name}: {cv_score.mean():.3f}({cv_score.std():.3f}) -> {cv_time:.2f}s | "
                  f"{train_score:.3f} & {eval_score:.3f} -> {train_test_time:.2f}s | "
                  f"{all_score:.3f} -> {all_time:.2f}s")
        
        # Create results dataframe
        results_df = pd.DataFrame({
            'cv_average': np.array([x.mean() for x in cv_results]),
            'train': np.array(train_scores),
            'test': np.array(eval_scores),
            'all': np.array(all_scores)
        }, index=names)
        
        times_df = pd.Series([np.mean(cv_times), np.mean(train_test_times), np.mean(all_times)], 
                          index=['cv', 'train/test', 'all'])
        
        # Plot results if requested
        if plot:
            self._plot_results(cv_results, names, results_df)
            
        return results_df, times_df, cv_results
    
    def _plot_results(self, cv_results, names, results_df, cv_yrange=(0.5, 1.0), hm_vvals=(0.5, 1.0, 0.75)):
        """Plot evaluation results."""
        sns.set(style="whitegrid")
        fig, ax = plt.subplots(1, 2, figsize=(15, 4))
        
        # Cross validation boxplot
        ax[0].set_title(f'{self.n_fold} Cross Validation Results')
        sns.boxplot(data=cv_results, ax=ax[0], orient="v", width=0.3)
        ax[0].set_xticklabels(names)
        sns.stripplot(data=cv_results, ax=ax[0], orient='v', color=".3", linewidth=1)
        ax[0].set_xticklabels(names)
        ax[0].xaxis.grid(True)
        ax[0].set(xlabel="")
        if cv_yrange:
            ax[0].set_ylim(cv_yrange)
        
        # Heatmap of scores
        sns.heatmap(results_df, vmin=hm_vvals[0], vmax=hm_vvals[1], center=hm_vvals[2],
                   ax=ax[1], square=False, lw=2, annot=True, fmt='.3f', cmap='Blues')
        ax[1].set_title('Accuracy Scores')
        
        sns.despine(trim=True, left=True)
        plt.tight_layout()
        plt.show()