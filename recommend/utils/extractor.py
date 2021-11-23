import pandas as pd

class Extractor:

    def get_items_interacted(self, person_id, interactions_df):
        interacted_items = interactions_df.loc[person_id]['content_id']
        return set(interacted_items if type(interacted_items) is pd.Series else [interacted_items])

