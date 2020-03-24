import copy
import qgrid
import pandas as pd
import matplotlib.pyplot as plt

from IPython.display import display, Markdown as md, clear_output
from ipywidgets import Output
from .wordclouder import WordClouder

from metrics.token import TokensManager


class WCListener():

    def __init__(self, sources, max_words=100):
        self.sources = sources
        self.max_words = max_words

    def listen(self, _range, editor, source, action):
        df = self.sources[source]

        df = df[(df.rev_time.dt.date >= _range[0]) &
                (df.rev_time.dt.date <= _range[1])]

        if action == 'Just Insertions':
            df = df[df['action'] == 'in']
        elif action == 'Just Deletions':
            df = df[df['action'] == 'out']

        if editor != 'All':
            df = df[df['name'] == editor]

        if len(df) == 0:
            display(md(f"**There are no words to build the word cloud.**"))
            return 0

        df_in = df[df['action'] == 'in']['token'] + '+'
        df_out = df[df['action'] == 'out']['token'] + '-'
        in_out = pd.concat([df_in, df_out])

        word_counts = in_out.value_counts()[:self.max_words]
        colors = {'+': '#003399', '-': '#CC3300'}

        # Create word cloud
        wc = WordClouder(word_counts, colors, self.max_words)

        try:
            wcr = wc.get_wordcloud()
            display(md(f"**Only top {self.max_words} most frequent words displayed.**"))

            # Revisions involved
            display(md(f"### The below token conflicts ocurred in a total of {len(df['rev_id'].unique())} revisions:"))

            # Plot
            plt.figure(figsize=(14, 7))
            plt.imshow(wcr, interpolation="bilinear")
            plt.axis("off")
            plt.show()

        except ValueError:
            display(
                md("Cannot create the wordcloud, there were zero conflict tokens."))

class WCActionsListener():
    
    def __init__(self, sources, token_source, max_words=100):
        self.sources = sources
        self.max_words = max_words
        self.token_source = token_source
        self._range1 = 0
        self._range2 = 1
        self.adds = None
        self.dels = None
        self.reins = None
        
    def revid_selection_change(self, change):
        with self.out2:
            clear_output()
            rev_selected = self.qgrid_selected_token.get_selected_df().reset_index()['rev_id'].iloc[0]

            url = f'https://en.wikipedia.org/w/index.php?title=TITLEDOESNTMATTER&diff={rev_selected}&diffmode=source'
            print(url)
                   
    def token_selection_change(self, change):
        with self.out1:
            clear_output()

            # Process the involved dataframe.
            token_selected = self.qgrid_token_obj.get_selected_df().reset_index()['token'].iloc[0]
            selected_token = self.ranged_token[self.ranged_token['token'] == token_selected]
            df_selected_token = selected_token.drop(['page_id', 'o_editor', 'token', 'o_rev_id', 'article_title'], axis=1)
            new_cols = ['token_id', 'action', 'rev_time', 'editor', 'rev_id']
            df_selected_token = df_selected_token[new_cols]
            df_selected_token['token_id'] = df_selected_token['token_id'].astype(str)
            df_selected_token['rev_id'] = df_selected_token['rev_id'].astype(str)
            df_selected_token.set_index('token_id', inplace=True)

            qgrid_selected_token = qgrid.show_grid(df_selected_token)
            self.qgrid_selected_token = qgrid_selected_token
            display(md(f'**With token *{token_selected}*, select one revision you want to investigate:**'))
            display(self.qgrid_selected_token)
            
            self.out2 = Output()
            display(self.out2)
            self.qgrid_selected_token.observe(self.revid_selection_change, names=['_selected_rows'])

    
    def listen(self, _range1, _range2, source, action):
        
        # For tokens.
        df_token = (self.token_source).copy()
        df_token = df_token[(df_token['rev_time'].dt.date >= _range1) & (df_token['rev_time'].dt.date <= _range2)]
        
        token_calculator = TokensManager(df_token, maxwords=self.max_words)
        if (self._range1 != _range1) | (self._range2 != _range2):
            add_actions, del_actions, rein_actions = token_calculator.token_survive()
                
            self._range1 = copy.copy(_range1)
            self._range2 = copy.copy(_range2)
            self.adds = add_actions
            self.dels = del_actions
            self.reins = rein_actions
            self.ranged_token = df_token
            
        else:
            pass
        
        tokens_action_no_ratio = token_calculator.get_all_tokens(self.adds, self.dels, self.reins, ratio=False)
        
        symbol_dict = {'adds': '+', 'adds_48h': '!', 'dels': '-', 'dels_48h': '@', 'reins': '*', 'reins_48h': '#'}
        if action == 'All':
            long_list = []
            tokens_for_wc = tokens_action_no_ratio.rename(symbol_dict, axis=1)
            for col in list(tokens_for_wc.columns):
                tokens_for_wc[col].index = tokens_for_wc[col].index + f'{col}'
                long_list.append(tokens_for_wc[col])
            df = pd.concat(long_list)
        else:
            symbol = symbol_dict[action]
            tokens_for_wc = tokens_action_no_ratio.rename({action: symbol}, axis=1)
            tokens_for_wc[symbol].index = tokens_for_wc[symbol].index + symbol    
            df = tokens_for_wc[symbol]

        if len(df) == 0:
            display(md(f"**There are no words to build the word cloud.**"))

        colors = {'+': '#003399', '!': '#0099ff', '-': '#CC3300', 
              '@': '#CC6633', '*': '#00ffcc', '#':'#00ff33'}

        # Create word cloud
        wc = WordClouder(df, colors, 5000)

        try:
            wcr = wc.get_wordcloud()
            display(md(f"**Only top {self.max_words} most frequent words displayed.**"))
            
            # Revisions involved
            #display(md(f"### The below tokens existed in a total of {len(df['rev_id'].unique())} revisions:"))

            # Plot
            plt.figure(figsize=(14, 7))
            plt.imshow(wcr, interpolation="bilinear")
            plt.axis("off")
            plt.show()

        except ValueError:
            display(
                md("Cannot create the wordcloud, there were zero actions."))
            
        tokens_action = token_calculator.get_all_tokens(self.adds, self.dels, self.reins)
        if len(tokens_action) != 0:
            qgrid_token_obj = qgrid.show_grid(tokens_action,grid_options={'forceFitColumns':False})
            self.qgrid_token_obj = qgrid_token_obj
            display(md('**Select one token you are interested in:**'))
            display(self.qgrid_token_obj)
            
            self.out1 = Output()
            display(self.out1)
            self.qgrid_token_obj.observe(self.token_selection_change, names=['_selected_rows'])            
            #return qgrid_token_obj
        else:
            display(md('**There are no words to build the table.**'))
            

        
            

        
        
        
            
