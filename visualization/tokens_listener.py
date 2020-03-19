import qgrid
import pandas as pd
from IPython.display import display, Markdown as md, clear_output

from metrics.token import TokensManager


class TokensListener:
    
    def __init__(self, source):
        self.source = source        

    def tokens_listener(self, range1, range2):
        """
        """
        df = (self.source).copy()
        df = df[(df['rev_time'].dt.date >= range1) & (df['rev_time'].dt.date <= range2)]

        token_calculator = TokensManager(df, maxwords=100)
        display(md('Loading data...'))
        add_actions, del_actions, rein_actions = token_calculator.token_survive()
        clear_output()
        tokens_action = token_calculator.get_all_tokens(add_actions, del_actions, rein_actions)

        if len(tokens_action) != 0:
            qgrid_obj = qgrid.show_grid(tokens_action,grid_options={'forceFitColumns':False})
            display(qgrid_obj)
        else:
            display(md('**There are no words to build the table.**'))
    
    
    
    