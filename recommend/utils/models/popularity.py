import pandas as pd



class PopularityModel:
    def model(self):
        #interaction_df = read_frame(Interaction.objects.all())
        interactions_df = pd.read_csv('recommend/files/interactions.csv')
        interactions_df.set_index('personId', inplace=True)
        popularity_df = interactions_df.groupby('contentId')['eventStrength'].sum(). \
                            sort_values(ascending= False).reset_index()
        return popularity_df
