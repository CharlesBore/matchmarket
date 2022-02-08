import re 
import json
import folium
import requests
import numpy as np
import pandas as pd
from PIL import Image
import streamlit as st
from io import BytesIO
import plotly.express as px
from requests.api import post
from wordcloud import STOPWORDS
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.figure_factory as ff
from plotly.subplots import make_subplots
from streamlit_folium import folium_static


#Définit le mode "large" du site : afin que l'ensemble de la page soit utilisée pour afficher les graphiques:
st.set_page_config(layout="wide")

#Pour mettre le logo MatchMarket dans la sidebar (console verticale de gauche):
st.sidebar.image("https://github.com/FlorianMimolle/matchmarket/blob/main/Streamlit/mjyLok-f_400x400.png?raw=true")

#Met les options cochables dans la sidebar pour afficher le tableau de donné ainsi que le menu soit graphique, soit cluster:
table = st.sidebar.checkbox("Afficher le Tableau de données ")
page = st.sidebar.radio("Page",("Graphique","Cluster"))

###################################################################GRAPHIQUE#####################################################################  
if page == "Graphique":
    #Liens du fichier :
    link = 'https://github.com/FlorianMimolle/matchmarket/raw/main/Streamlit/df.csv.zip'
    df = pd.read_csv(link,compression="zip",low_memory=False)

    #Pour sélectionner quels type de campagne on souhaite voir (dans la sidebar): 
    Type_Campaign = st.sidebar.radio("Sélectionner le Type de Campagne à analyser :",
                                     ("All","Mode","Déco","Cosmétique"))
    if Type_Campaign == "Mode":
        df_result = df[df["type_Campaign"]=="Mode"]
    if Type_Campaign == "Déco":
        df_result = df[df["type_Campaign"]=="Deco"]
    if Type_Campaign == "Cosmétique":
        df_result = df[df["type_Campaign"]=="Cosmetique"]
    if Type_Campaign == "All": #Pour voir l'ensemble des données
        df_result = df
     #Pour sélectionner quels campagnes_id on souhaite voir (dans la sidebar): 
    liste_campaign_id = ["All"] #On créer une liste contenant la valeur "All" 
    for id in sorted(df_result["campaign_id"].unique()): #On rajoute à la liste contenant "All" les campaign_id du type de campaign sélectionné
        liste_campaign_id.append(str(id))
    Campaign_id = st.sidebar.selectbox('Quelle campaign_id souhaitez-vous analyser ? ',liste_campaign_id) #On affiche le selectbox contenant les campaign_id et "All"
    if Campaign_id != "All": #Si le Campaign_id sélectionné est différent de "All" alors on filtre le dataframe sur l'id sélectionné
        df_result = df_result[df_result["campaign_id"]==int(Campaign_id)]
        
    #Si On coche table, alors on affiche le dataframe résultant:
    if table:
        st.write("Tableau de données : ")
        df_result
    campaign_wc = df_result["type_Campaign"].iloc[0]
    if len(df_result["type_Campaign"].unique())==1:
        if campaign_wc =="Cosmetique":
            url = requests.get("https://github.com/FlorianMimolle/matchmarket/blob/main/Streamlit/black-white-silhouette-perfume-bottle-600w-1037202859.png?raw=true")
        elif campaign_wc =="Deco":
            url = requests.get("https://github.com/FlorianMimolle/matchmarket/blob/main/Streamlit/Sans%20titre.png?raw=true")
        else: 
            url = requests.get("https://github.com/FlorianMimolle/matchmarket/blob/main/Streamlit/black-dress-clipart.jpg?raw=true")
    else:
        url = requests.get("https://github.com/FlorianMimolle/matchmarket/blob/main/Streamlit/black-dress-clipart.jpg?raw=true")
    
    def couleur(*args, **kwargs):
        import random
        return "rgb(250, 0, {})".format(random.randint(100, 255))
    
    img = Image.open(BytesIO(url.content))
    mask = np.array(img)      
    stopwords = set(STOPWORDS) # créer la liste des stopwords
    stopwords.update(["à", "de", "en", "pièce", "2p"])
    text = " ".join(article for article in df_result['product name']) # transformer en liste la colonne 'product name'
    text_new = re.sub(pattern='[^\w\s]', repl=' ', string=text) # enlever les chiffres
    # Créer un image de wordcloud
    wordcloud = WordCloud(stopwords=stopwords, 
                          background_color="white", 
                          max_words=30, 
                          collocations=False, 
                          contour_color='#FFCF00',
                          contour_width = 0.00001,
                          min_font_size = 7,
                          prefer_horizontal = 1,
                          mask = mask).generate(text_new)
    # Afficher le wordcloud
    fig, ax = plt.subplots(1,1)
    ax.imshow(wordcloud.recolor(color_func=lambda *args, **kwargs: (255, 0, 205)), 
              interpolation='bilinear')
    ax.axis("off")
    st.sidebar.pyplot(fig.figure)

    #Pour sélectionner le graphique que l'on souhaite voir : 
    type_graphique = st.selectbox("",("Carte de France","Carte par Département","Matières","Couleur"))
    
    #######################GRAPHIQUE CARTE DE FRANCE : 
    if type_graphique =="Carte de France":
        df_result["Département"] = df_result["zipcode"].apply(lambda x : x[:2]) #On créé la colonne département à partir des deux premiers chiffres du zipcode
        df_result["Urbain"] = df_result["Urbain"]*100 #On met en pourcentage la colonne "Urbain"
        client_loca_df = df_result[["user id","Département","Age","Urbain"]].drop_duplicates("user id") #On séléctionne les colonnes qui nous interesse et On élimine les duplicats de user pour ne garder qu'une valeur d'âge et d'urbain par user
        client_loca_df = client_loca_df.groupby("Département").agg({"user id":["count"], #On regroupe les informations des user par département (on compte les user_id pour avoir le nb_personne, on moyenne l'age et urbain)
                                                           "Age":["mean"],
                                                           "Urbain":["mean"]})
        vote_loca_df = df_result[["Département","action"]] #On créé un df avec département et action (dans client_loca_df on supprime les duplicats d'user donc on perd l'information des différents votes par user, on est donc obligé de recréer ce dataframe)
        vote_loca_df["action"] = vote_loca_df["action"].apply(lambda x : 0 if x =="dislike" else 1) #On numérise la colonne action
        vote_loca_df = vote_loca_df.groupby("Département").agg(lambda x : round(x.mean()*100,2)) #On regroupe les informations par département en calculant le % de like
        votant_df = df_result[["Département","action"]]#On créé un df avec département et action (dans client_loca_df on supprime les duplicats d'user donc on perd l'information des différents votes par user, on est donc obligé de recréer ce dataframe)
        votant_df = votant_df.groupby("Département").agg("count") #Avoir le nombre de vote
        df_result = pd.merge(client_loca_df,vote_loca_df,left_on = "Département",right_on = "Département") #on regroupe les deux dataframes pour avoir toutes les informations par département
        df_result = pd.merge(df_result,votant_df,left_on = "Département",right_on = "Département") #on regroupe les deux dataframes pour avoir toutes les informations par département
        df_result = df_result.drop("na") #On supprime les départements inconnu
        df_result = df_result.reset_index() #On met les index "Département" en colonne
        df_result.columns = ["Département","nb_Client","Âge","Urbain","%Like","nb_Vote"] #On renomme les colonnes
        if table:
            st.write("Tableau de données du graphique :")
            df_result
        
        #On import le fichier geojson qui sert à tracer les départements: 
        state_geo = json.loads(requests.get("https://france-geojson.gregoiredavid.fr/repo/departements.geojson").text)
        for idx in range(0,len(state_geo["features"])): #Pour tout les pays du fichier json on créé la donnée vide nb_wines
            state_geo["features"][idx]['properties']["nb_Client"]= 0
            state_geo["features"][idx]['properties']["Âge"]= 0
            state_geo["features"][idx]['properties']["Urbain"]= 0
            state_geo["features"][idx]['properties']["%Like"]= 0
            state_geo["features"][idx]['properties']["nb_Vote"]= 0
        for idx in range(0,len(state_geo["features"])): #Pour tout les départements du fichier json:
            for index in range(0,len(df_result)): #Pour tout les départements du df_result :
                if str(state_geo["features"][idx]['properties']['code'])==str(df_result.iloc[index,0]): #Si les deux idx et index concorde : alors on modifie le fichier Json pour ajouter les valeurs aux départements
                    state_geo["features"][idx]['properties']['nb_Client']= \
                    int(df_result['nb_Client'][index]) #Ajout du nombre de client dans le fichier Json
                    state_geo["features"][idx]['properties']['Âge'] = \
                    round(df_result['Âge'][index],2) #Ajout de l'age moyen des clients dans le fichier Json
                    state_geo["features"][idx]['properties']['Urbain'] = \
                    str(round(df_result['Urbain'][index],2)) + " %" #Ajout de la provenance des clients dans le fichier Json
                    state_geo["features"][idx]['properties']['%Like'] = \
                    str(round(df_result['%Like'][index],2))+" %, nb_Vote : " + str(df_result['nb_Vote'][index]) #Ajout du %Like moyen des clients dans le fichier Json

        #On créé un dictionnaire pour faire la traduction entre les noms de colonne et Comment on veut faire apparaître sur la page streamlit:
        dicts = {"Nombre de Praedicters":'nb_Client',
                "Âge moyen": 'Âge',
                "Pourcentage de Preadicters venant du milieu Urbain": 'Urbain',
                "Pourcentage de Like": '%Like'}
        #Selecteur pour sélectionner la valeur à afficher sur la carte:
        select_data = st.radio("",
                               ("Nombre de Praedicters", "Âge moyen","Pourcentage de Preadicters venant du milieu Urbain",'Pourcentage de Like'))
        #On modifie la couleur si %Like en vert/Jaune/rouge :
        if select_data == "Pourcentage de Like":
            couleur = "RdYlGn"
        else: #Sinon, on met la couleur dans les tons roses:
            couleur = "RdPu"
        #On créé la carte de base:
        m = folium.Map(tiles="cartodb positron", 
                    location=[47, 2], 
                    zoom_start=6,)
        #on ajoute les informations sur la carte : 
        maps= folium.Choropleth(geo_data = state_geo, #Fichier Geoson pour afficher les départements
                                data = df_result,
                                columns=['Département',dicts[select_data]], #On met la valeur sélectionnée
                                key_on='properties.code', #On relie le fichier Geoson au df_result par le code dans "properties.code" du fichier Geoson
                                fill_color=couleur, #On met la couleur en fonction de la valeur a afficher
                                fill_opacity=0.8, #Rend la forme du département légerement transparant pour voir un peu les indications de la carte de base
                                line_opacity=0.2,
                                legend_name=dicts[select_data] #Change le nom de la légende
                                ).add_to(m)
        #On ajoute une bulle de légende au survole de la souris sur le département : 
        maps.geojson.add_child(folium.features.GeoJsonTooltip
                                        (aliases=["Département","n° Département",select_data], #Modifie les aliases (partie gauche de la bulle d'info)
                                        fields=["nom","code",dicts[select_data]], #On modifie les valeurs (partie droite de la bulle d'info)
                                        labels=True)) #Pour afficher l'aliases

        folium_static(m)
    
    #######################GRAPHIQUE CARTE DES DEPARTEMENTS :     
    if type_graphique =="Carte par Département":
        df_result["Département"] = df_result["zipcode"].apply(lambda x : x[:2]) #On créé la colonne département à partir des deux premiers chiffres du zipcode
        df_result["Urbain"] = df_result["Urbain"]*100 #On met en pourcentage la colonne "Urbain"
        df_result = df_result[df_result["Département"] != "na"] #On enlève les lignes où le département est inconnu
        df_result = df_result[df_result["Département"] != "98"] #On enlève les lignes où le département est inconnu
        #Sélecteur du numéro de département:
        Département = st.selectbox('Quel numéro de département souhaitez-vous ? ', tuple(sorted(df_result["Département"].unique())))
        postal_df = df_result[df_result["Département"] == str(Département)] #On filtre sur le département choisi
        #On créé la première partie du dataframe:
        client_postal_df = postal_df[["zipcode","user id","Coordonnées","Age"]].drop_duplicates("user id") #On séléctionne les colonnes qui nous interesse et On élimine les duplicats de user pour ne garder qu'une valeur d'âge et d'urbain par user
        client_postal_df = client_postal_df.groupby("zipcode").agg({"user id" : ["count"], #On compte le nombre de valeur unique pour connaître le nombre de client
                                                    "Coordonnées" : ["first"],#Première valeur du zipcode (les autres valeurs du même zipcode sont identiques)
                                                    "Age":["mean"]}) #On moyenne l'age des clients
        #On créé la deuxième partie du dataframe:
        vote_postal_df = postal_df[["zipcode","action"]]
        vote_postal_df["action"] = vote_postal_df["action"].apply(lambda x : 0 if x =="dislike" else 1) #On numérise la colonne action
        vote_postal_df = vote_postal_df.groupby("zipcode").agg({"action":[lambda x : round(x.mean()*100,2)]}) #Pourcentage de Like
        #On rejoint les deux dataframes:
        postal_df = pd.merge(client_postal_df,vote_postal_df,left_on = "zipcode",right_on = "zipcode")
        postal_df = postal_df.reset_index() #On sort les index zipcode pour que cela devienne une colonne
        postal_df.columns = ["zipcode","nb_Personne","Coordonnées","Age","%Like"] #On renomme les colonnes
        postal_df["color"] = postal_df["%Like"].apply(lambda x : "#f24343" if x < 30 #On attribue la couleur pour Like 
                                                            else "#FFCF00" if x < 70
                                                            else "#27d830")
        postal_df = postal_df[postal_df["Coordonnées"].isnull() == False] #On supprime les lignes où le zipcode n'a pas été trouvé
        postal_df["Coordonnées"] = postal_df["Coordonnées"].apply(lambda x : x.replace("[","")).apply(lambda x : x.replace("]","")).apply(lambda x : x.replace("'","")) #On supprime les caractères non souhaités
        postal_df["Coordonnées"] = postal_df["Coordonnées"].apply(lambda x : x.split(","))#On split à chaque virgule (pour séparer longitude et latitude)
        postal_df["lon"] = postal_df["Coordonnées"].apply(lambda x : x[0]) #On créé la colonne longitide
        postal_df["lat"] = postal_df["Coordonnées"].apply(lambda x : x[1]) #On créé la colonne latitude
        lon_mean = postal_df["lon"].astype(float).mean() #On définie la longitide moyenne du df pour centré la carte au bon endroit
        lat_mean = postal_df["lat"].astype(float).mean() #On définie la longitide moyenne du df pour centré la carte au bon endroit
        #On affiche la table du graphique si coché :
        if table:
            st.write("Tableau de données du graphique :")
            postal_df
        #On génère la carte basique    
        m = folium.Map(location=[lon_mean, lat_mean], #Centrée sur lat et long mean du département choisi
                       zoom_start=8, 
                       tiles='cartodb positron')
        for zipcode_i in range(len(postal_df)): #Pour chacun des zipcode du dataframe :
            #on défini le texte à mettre dans l'infobulle
            texte = f"<p>{postal_df.iloc[zipcode_i,0]}<br /> \
            nb de Preadicters : {str(postal_df.iloc[zipcode_i,1])}<br/> \
            nb de Like : {str(round(postal_df.iloc[zipcode_i,4],2))+ ' %'}<br/> \
            moyenne d'âge : {str(round(postal_df.iloc[zipcode_i,3],2))}</p>" 
            #On place le marqueur sur la carte correspondant au zipcode_i  
            folium.Marker(location = postal_df.iloc[zipcode_i,2], #Localisation (avec les coordonnées lat long)
                          popup = folium.Popup(texte, #On met le texte défini en infobulle
                                               max_width=450), #Taille de l'infobulle
                          icon=folium.Icon(color = "lightgray", #Défini la couleur du marqueur sur gris
                                           icon_color=postal_df.iloc[zipcode_i,5], #Défini la couleur du bonhomme du marqueur en fonction du like
                                           icon = "user") #Défini la forme du bonhomme
                          ).add_to(m)
        #On affiche les départements sur la carte (en jaune transparant pour ne pas surcharger);
        choropleth = folium.Choropleth(geo_data="https://france-geojson.gregoiredavid.fr/repo/departements.geojson", 
                                       name="choropleth",
                                       fill_color="#FFCF00",
                                       fill_opacity=0.1
                                       ).add_to(m)

        #Ajouter l'infobulle pour le département:
        style_function = "font-size: 10px"#Défini la taille de police
        choropleth.geojson.add_child(folium.features.GeoJsonTooltip(['nom']+["code"],
                                                                    style=style_function,
                                                                    labels=False)
                                     )
    
        folium_static(m)
    
    #######################GRAPHIQUE DES MATIERES :  
    # On affiche la table Matières si l'onglet Matières a été choisi
    if type_graphique =="Matières":  
        # enlever les crochets et virgules de la colonne Matières
        df_result['material'] = df_result['material'].apply(lambda x: x.replace('[','')).apply(lambda x: x.replace(']','')).apply(lambda x: x.replace("'",'')).apply(lambda x: x.replace(",",' '))
        # créer un nouveau dataframe en groupant les articles par matières et action(like/dislike)
        df_total = df_result.groupby(["material", 'action'])\
            .count()[["product name"]]\
            .unstack(level=-1)\
            .sort_values(by=('product name','like'))\
            .tail(10)
        # transformer le dataframe de multi-index en mono-index pour faire du plotly
        df_total.columns = df_total.columns.map('_'.join)
        # afficher le dataframe si l'on choisit de regarder le table
        if table:
            st.write("Tableau de données du graphique :")
            df_total
        # créer des graphiques affichant le pourcentage de like et dislike en fonction de matières
        fig = go.Figure(data=[
                go.Bar(name= 'Like', # créer la barre des Like
                       y=df_total.index.get_level_values(0), # l'axe des matières
                       x = df_total['product name_like'], # l'axe du nombre de Like
                       orientation='h', # mettre l'orientation à l'horizontal
                       marker=dict(color = 'gold')), # choisir la couleur jaune
                go.Bar(name= 'Dislike', # créer la barre des Dislike
                       y=df_total.index.get_level_values(0), # l'axe des matières
                       x = df_total['product name_dislike'], # l'axe du nombre de Dislike
                       orientation='h', # mettre l'orientation à l'horizontal
                       marker=dict(color = 'deeppink'))])  # choisir la couleur rose                          
        # personnaliser le graphique
        fig.update_layout(barmode='group', # mode de disposition des barres (côte à côte)
                            title_text=f'Nombre de votes pour les campagnes de type {Type_Campaign}', # titre de graphique
                            font = dict(size = 14), # taille du police
                            xaxis_title = "Nombre de votes", # titre de l'axe x
                            yaxis_title = "Matière",# titre de l'axe y
                            width = 1000,
                            height = 500) 
        st.plotly_chart(fig)  #afficher le graphique        

    #######################color########################### :    
    if type_graphique == "Couleur":
        col1, col2 = st.columns(2)# pour avoir deux graphique cote à cote 
        with col1:
            df1= df_result.groupby(["campaign_id","action"])\
                            .sum()[["neutre","vif"]].unstack()\
                            .sort_values(by =["campaign_id"],ascending = True)# crée un dataframe regrouper par campagne_id et action de votes pour les couleurs
            df1['neutre', 'dislike']=df1['neutre', 'dislike']*(-1)# multiplié par -1 pour les colonnes dislikes pour avoir 2 coté like et dislikes sur le graphique
            df1['vif', 'dislike']=df1['vif', 'dislike']*(-1)
            df1.columns = df1.columns.map('_'.join)
            if table:
                st.write("Tableau de données du graphique :")# pour afficher la table qu'on viens de crée
                df1 
            fig = go.Figure(data=[
                go.Bar(name= 'Like-neutre', y=df1.index.get_level_values(0), x = df1['neutre_like'], orientation='h',marker=dict(color = 'lawngreen')),# pour mettre la couleur lawngreen pour les bars like-neutre
                go.Bar(name= 'Dislike-neutre', y=df1.index.get_level_values(0), x = df1['neutre_dislike'], orientation='h',marker=dict(color = 'pink')),#pour mettre la couleur pink pour les bars dislike-neutre
                go.Bar(name= 'Like-vif', y=df1.index.get_level_values(0), x = df1['vif_like'], orientation='h',marker=dict(color = 'gold')),#pour mettre la couleur gold pour les bars like-vif
                go.Bar(name= 'Dislike-vif', y=df1.index.get_level_values(0), x = df1['vif_dislike'], orientation='h',marker=dict(color = 'deeppink'))#pour mettre la couleur deeppink pour les bars dislike-vif
            ])                              
            fig.update_layout(barmode='group',
                              title_text="Nombre de votes like, dislike selon les couleurs<br>et par campagne ",# titre du graphique
                              font = dict(size = 14),
                              xaxis_title = "Nombre de votes",# titre pour x
                              yaxis_title = "campagne_id ",# titre pour y
                              width=600,
                              height=500)
            st.plotly_chart(fig)  
        with col2:
            df_result['color'] = df_result['color'].apply(lambda x: x.replace('[','')).apply(lambda x: x.replace(']','')).apply(lambda x: x.replace("'",''))# dans la table résult les couleurs apparaitre sous forme de list exemple [noir], on vas donc enlever les crochés pour que ca  devient noir
            df1=  df_result.groupby(["color", 'action'])\
                          .count()[["product name"]]\
                          .unstack()\
                          .sort_values(by=('product name','dislike'))\
                          .tail(10)# pour avoir une table avec les 10 coleurs les plus présenter et les votes pour ces couleurs
            df1.columns = df1.columns.map('_'.join)
            if table:
                st.write("Tableau de données du graphique :")# pour afficher la table en fonction des couleurs les plus présenter et les nb de votes 
                df1
            fig = go.Figure(data=[
                go.Bar(name= 'Like', y=df1.index.get_level_values(0), x = df1['product name_like'], orientation='h',marker=dict(color = 'gold')),
                go.Bar(name= 'Dislike', y=df1.index.get_level_values(0), x = df1['product name_dislike'], orientation='h',marker=dict(color = 'deeppink'))
            ])                              
            fig.update_layout(barmode='group',
                              title_text="Top 10 des couleurs les plus présentes",
                              font = dict(size = 14),
                              xaxis_title = "Nombre de votes",
                              yaxis_title = "couleur ",
                              width=600,
                              height=500)
            st.plotly_chart(fig)

####################################################################CLUSTERS#####################################################################  
if page == "Cluster":
    #Puis défini le link à prendre en fonction du choix : 
    Type_Campaign = st.sidebar.radio("Sélectionner le Type de Campagne à clusteriser :",("Mode","Déco","Cosmétique"))
    if Type_Campaign == "Mode":
        link = "https://raw.githubusercontent.com/FlorianMimolle/matchmarket/main/Streamlit/Fashion.csv"
    if Type_Campaign == "Déco":
        link = "https://raw.githubusercontent.com/FlorianMimolle/matchmarket/main/Streamlit/Deco.csv"
    if Type_Campaign == "Cosmétique":
        link = "https://raw.githubusercontent.com/FlorianMimolle/matchmarket/main/Streamlit/Cosmetique.csv" 
    df = pd.read_csv(link,low_memory=False) #Puis défini le df en fonction du link choisi
    
    #Compte le nombre de cluster différent dans la table sélectionnée (car le nombre de cluster peut varier entre les tables) et les mets en format liste:
    cluster = []
    for i in range(1,1+len(df["cluster"].unique())): #Pour cela, il regarde le nombre de valeur unique dans la colonne "cluster"
        cluster.append("Cluster "+str(i))
        
    #Parmis les différents cluster de la table séléctionnées, quels cluster choisir (multiselect pour afficher plusieurs cluster en même temps et les comparer):
    options = st.sidebar.multiselect('Quel cluster souhaitez-vous visualiser ?',
                                     cluster,
                                     ['Cluster 1']) #Choix présélectionné à l'ouverture du fichier
    
    #Créé le dataframe df_result correspondant à la table séléctionnée (Mode/déco/Cosmétique) et filtrée sur le/les clusters choisi:
    df_result = pd.DataFrame(columns = df.columns.tolist())#Pour cela, on créé d'abbord un dataframe vide avec le nom des colonnes du df globale
    compteur = 1
    for clusteur_i in cluster: #Puis pour chacun des clusters dans les clusters possibles,
        if clusteur_i in options : #Si le cluster_i est dans le/les clusters choisi par l'utilisateur,
            df_result = pd.concat([df_result,df[df["cluster"]==compteur]]) #Alors on concatène le df_result (vide au premier tour), avec le df filtré sur le cluster_i
        compteur += 1 #Le compteur est nécessaire car dans la table les clusteurs sont identifiés 1,2,... alors que dans les options c'est cluster1,cluster2,...
        
    #Si on sélectionne l'option d'afficher le tableau de données, alors on affiche le dataframe résultant :
    if table:
        st.write("Tableau de données : ")
        df_result
    
    #Ecris le titre 1 de la page : 
    a = " et ".join(re.findall('\d',str(options))) #Pour afficher les numéros des clusters choisis sous le format 1 et 2 et 3... (re.findall('\d) permet de récuperer uniquement les chiffres des clusters)
    st.title(f"Profil du clusters {a}, soit : {len(df_result)} Praedicters")
    
    #Si le dataframe n'est pas vide alors on affiche les graphiques ... s'il est vide (pas de cluster séléctionnés par exemple) : alors on ne fait rien
    if len(df_result)>0:  
        
        col1,col2,col3 = st.columns((1,2,2))
        ##############GRAPHIQUE DISTRIBUTION DE L'AGE : 
        with col1:
            representation = st.radio("Représentation",("Courbe normalisée","histogramme"))
            if representation == "Courbe normalisée":
                Normalise = False
            else:
                Normalise = True
        with col2: 
            hist_data = []
            group_labels = []
            for cluster_i in sorted(options): #Pour chacun des clusters choisis (on les tris pour que la couleur d'un cluster soit identique sur tous les graphiques de la page)
                nbr = int("".join(re.findall("\d",cluster_i))) #On récupère le numeros du cluster (re.findall('\d) permet de récuperer uniquement les chiffres du cluster)
                x = df_result[df_result["cluster"]==nbr]["Age"] #On récupère la liste des âges du cluster_i
                hist_data.append(x) #On ajoute la liste d'age à une liste globale qui servira à la création du graphique
                group_labels.append(cluster_i) #On ajoute le cluster aux labels afin de créer la légende
            fig = ff.create_distplot(hist_data, #Liste des âges
                                    group_labels, #Labels pour legende
                                    histnorm = "", #Pour éviter la normalisation quand histbar
                                    show_hist=Normalise, #Cache les histogrammes (pour n'afficher que la courbe, sinon c'est vite illisible)
                                    show_rug=False, #Cache la règlette affichée par défaut dans plotly mais qui n'apporte rien
                                    colors = ["gold","deeppink","orange","lemonchiffon"]) #Liste de couleur pour identifier chacun des clusters
            fig.update_layout(title_text="Distribution de l'Age", #Titre du graphique
                              font = dict(size = 14),#Pour mettre une police un peu plus grosse
                              width = 470,
                              height = 400,
                              yaxis_title = "Nombre de clients", #Label de y
                              xaxis_title = "Âge") #Label de x
            st.plotly_chart(fig) 
        ##############GRAPHIQUE POURCENTAGE DE MILIEU URBAIN :
        with col3:
            labels = ["Supérieure à 5000 hab","Inférieure à 5000 hab"] #Label pour la légende
            values = np.array([round(df_result["Urbain"].mean()*100,2),100-round(df_result["Urbain"].mean()*100,2)]) #Créer un array avec le% de personnes urbains et le % de personnes rurales
            fig = go.Figure(data=[go.Pie(labels=labels, #Créer le camembert avec la legénde
                                     values=values, #les deux % (ruraux et urbain)
                                     hole=.5, #Pour faire un donut plutôt qu'un camembert
                                     marker_colors=["deeppink","gold"], #Met les deux couleurs Urbain/Rural
                                     pull=[0.2, 0])], #pour exploder (décaller) la part Urbain 
                            layout={"title":"Provenance des Praedicters"}) #Titre du graphique
            fig.update_layout(font = dict(size = 14),
                              width = 470,
                              legend_title = "Population de la commune") #Titre du bloc légende
            st.plotly_chart(fig)
        
        ##############GRAPHES STYLES PREF EN FONCTION DE LA TRANCHE D'AGE DES USERS :
        col1,col2 = st.columns((1,4))
        with col1:
            pref_for_ages = st.radio("Préférences exprimées",
                                     ('Préférence stylistique', 'Marques de Beauté préférées',"Marques de Mode préférées")) #Bouton pour la sélection des préférences de styles ou de marques choisies par les praedicters
        with col2:
            df_agescut = df_result.copy() #Création d'un nouveau DataFrame pour la transformation des données de sorte à obtenir des tranches d'âges par praedicter
            df_agescut['Age'] = pd.cut(df_agescut['Age'], 
                                       bins = [0, 20, 25, 30, 40, 60, 100], #Nouvelles tranches d'âges : 0-20, 20-25, 25-30, 30-40, 40-60 et 60-100
                                       labels=["moins de 20 ans", "20 à 24 ans", "25 à 29 ans", "30 à 39 ans", "40 à 59 ans", "60 ans et plus"]) #Labels des tranches d'âges correspondants aux bins
            if pref_for_ages == 'Préférence stylistique': #Condition : si l'utilisateur a sélectionné les préférences stylistiques (variable pref_for_ages précédemment définie par le bouton radio)
                df_agescut = df_agescut.groupby('Age')[['Casual, Urbancool, Streetwear', 'Chic, Smart, Working Girl', 'Rock, Gothique', 'Engagée, Made in France', 'Fatale', 'Bohême, Romantique', 'Vintage, Kawaii', 'Inconnu']].agg('sum')
                #Regroupement par ages
                df_agescut_new = df_agescut.copy() #On créé une nouvelle table qui permettra de calculer le pourcentage des observations par style et par tranche d'âge rapportées au nombre total d'observations par tranche d'âge
                for e in df_agescut.index: #On se sert d'une boucle pour récupérer la somme des observations associée à chaque tranche d'âge. Sur la table, 1 ligne = 1 tranche d'âge
                    somme = df_agescut.loc[e,:].sum() #ici, e = tranche d'âge (ligne)
                    for i in df_agescut.columns: #Pour chaque ligne, soit chaque tranche d'âge, on calcule le % en divisant chaque observation par style et par tranche d'âge par le nombre total d'observations
                        df_agescut_new.loc[e,i] = df_agescut.loc[e,i]/somme*100 #ici, e = tranche d'âge (ligne) et i = style (colonne)
                df_agescut_new.reset_index(inplace=True) #On fait basculer les tranches d'âge précédemment situées en index dans les colonnes de la table
                fig = px.bar(df_agescut_new, #Création d'un stacked barplot, orienté à l'horizontal. x correspond au nom des colonnes et y à la tranche d'âge
                             y = "Age", 
                             x = ['Casual, Urbancool, Streetwear', 'Chic, Smart, Working Girl', 'Rock, Gothique', 'Engagée, Made in France', 'Fatale', 'Bohême, Romantique', 'Vintage, Kawaii', 'Inconnu'], 
                             orientation='h', 
                             color_discrete_sequence= px.colors.sequential.Plasma_r)
                fig.update_layout(title = "Préférences stylistique en fonction de la tranche d'âge des utilisateurs", #Ajout du titre du graphe
                              xaxis_title = "Pourcentage d'utilisateurs", #titre des axes
                              yaxis_title = "Tranches d'âges des utilisateurs",
                              legend_title = "Préférence stylistique", #titre de la légende 
                              height = 400, #dimensions du graphe
                              width = 900,
                              font = dict(size = 14)) #taille de la police
                st.plotly_chart(fig)
            elif pref_for_ages == "Marques de Beauté préférées" : #Condition : si l'utilisateur a sélectionné les marques de beauté (variable pref_for_ages précédemment définie par le bouton radio)
                df_agescut = df_agescut.groupby('Age')[['access_brand', 'mass_brand', 'premium_brand', 'hdg_brand', 'luxe_brand', 'bio_brand']].agg('sum') #Regroupement par ages
                df_agescut.columns = ["Access","Mass","Premium","Haut de Gamme","Luxe","Bio"]
                df_agescut_new = df_agescut.copy() #On créé une nouvelle table qui permettra de calculer le pourcentage des observations par marque et par tranche d'âge rapportées au nombre total d'observations par tranche d'âge
                for e in df_agescut.index: #On se sert d'une boucle pour récupérer la somme des observations associée à chaque tranche d'âge. Sur la table, 1 ligne = 1 tranche d'âge
                    somme = df_agescut.loc[e,:].sum() #ici, e = tranche d'âge (ligne)
                    for i in df_agescut.columns: #Pour chaque ligne, soit chaque tranche d'âge, on calcule le % en divisant chaque observation par marque et par tranche d'âge par le nombre total d'observations
                        df_agescut_new.loc[e,i] = df_agescut.loc[e,i]/somme*100 #ici, e = tranche d'âge (ligne) et i = gamme de produit (colonne)
                df_agescut_new.reset_index(inplace=True) #On fait basculer les tranches d'âge précédemment situées en index dans les colonnes de la table
                fig = px.bar(df_agescut_new, #Création d'un stacked barplot, orienté à l'horizontal. x correspond au nom des colonnes (gammes) et y à la tranche d'âge
                             y = "Age", 
                             x = ['Access', 'Mass', 'Premium', 'Haut de Gamme', 'Luxe', 'Bio'], 
                             orientation='h', 
                             color_discrete_sequence= px.colors.sequential.Plasma_r)
                fig.update_layout(title = "Gamme de marques préférées en fonction de la tranche d'âges des utilisateurs", #Ajout du titre du graphe
                              xaxis_title = "Pourcentage d'utilisateurs", #titre des axes
                              yaxis_title = "Tranche d'âges  des utilisateurs",
                              legend_title = "Catégories préférencielles",  #titre de la légende
                              height = 400, #dimensions du graphe
                              width = 900,
                              font = dict(size = 14)) #taille de la police
                st.plotly_chart(fig)
            else : #Condition : si l'utilisateur a sélectionné les marques de mode (variable pref_for_ages précédemment définie par le bouton radio)
                df_agescut = df_agescut.groupby('Age')[['access_mode', 'mass_mode', 'premium_mode', 'hdg_mode',"prestige_mode", 'luxe_mode', "vintage_mode","eco_responsable_mode"]].agg('sum')
                df_agescut.columns = ["Access","Mass","Premium","Haut de Gamme","Prestige","Luxe","Vintage","Eco Responsable"]
                df_agescut_new = df_agescut.copy() #On créé une nouvelle table qui permettra de calculer le pourcentage des observations par marque et par tranche d'âge rapportées au nombre total d'observations par tranche d'âge
                for e in df_agescut.index: #On se sert d'une boucle pour récupérer la somme des observations associée à chaque tranche d'âge. Sur la table, 1 ligne = 1 tranche d'âge
                    somme = df_agescut.loc[e,:].sum()
                    for i in df_agescut.columns: #Pour chaque ligne, soit chaque tranche d'âge, on calcule le % en divisant chaque observation par marque et par tranche d'âge par le nombre total d'observations
                        df_agescut_new.loc[e,i] = df_agescut.loc[e,i]/somme*100 #ici, e = tranche d'âge (ligne) et i = gamme de produit (colonne)
                df_agescut_new.reset_index(inplace=True) #Création d'un stacked barplot, orienté à l'horizontal. x correspond au nom des colonnes (gammes) et y à la tranche d'âge
                fig = px.bar(df_agescut_new, 
                             y = "Age", 
                             x = ["Access","Mass","Premium","Haut de Gamme","Prestige","Luxe","Vintage","Eco Responsable"], 
                             orientation='h', 
                             color_discrete_sequence= px.colors.sequential.Plasma_r)
                fig.update_layout(title = "Gamme de marques préférées en fonction de la tranche d'âge des utilisateurs", #Ajout du titre du graphe
                              xaxis_title = "Pourcentage d'utilisateurs", #titre des axes
                              yaxis_title = "Tranches d'âges  des utilisateurs",
                              legend_title = "Catégories préférencielles", #titre de la légende 
                              height = 400, #dimensions du graphe
                              width = 900,
                              font = dict(size = 14)) #taille de la police
                st.plotly_chart(fig)
        
        col1,col2,col3 = st.columns(3)
        ##############GRAPHIQUE STYLE PREFERENCE :        
        with col1:
            df_style = df_result[["Casual, Urbancool, Streetwear","Chic, Smart, Working Girl","Rock, Gothique","Engagée, Made in France","Fatale","Bohême, Romantique","Vintage, Kawaii","Inconnu","cluster"]] #Créé un dataframe avec que les colonnes nécessaires     
            df_style = df_style.groupby("cluster").mean().reset_index() #Regroupe les informations par cluster (aggrégation : moyenne)
            categories=["Casual,UrbanCool,Streetwear","Chic, Smart, Working Girl","Rock, Gothique","Engagée, Made in France","Fatale","Bohême, Romantique","Vintage, Kawaii","Inconnu"] #Créer une liste de label pour la légende
            couleur = ["gold","deeppink","orange","lemonchiffon"] #Créer la liste de couleur pour différencier les clusters
            #Pour chacun des clusters choisis (df_style est créé à partir de df_result, donc les clusters non choisis sont déjà enlevés)
            data = []
            for cluster_i in range(len(df_style["cluster"])): #Pour chacun des clusters dans les clusters séléctionnés
                liste = []
                for i in range(1,9): #Pour chacune des colonnes styles du df_style
                    liste.append(df_style.iloc[cluster_i,i]) #On ajoute à la liste les différentes moyennes corréspondant aux différents styles pour chacun des clusters
                data.append(go.Bar(name=f'cluster {df_style.iloc[cluster_i,0]}', #On créer différents graphiques en bar, name : sert à identifier les différents clusters
                                   x=categories, #Pour les labels en x
                                   y=liste, #Pour les valeurs
                                   marker_color = f"{couleur[cluster_i]}")) #Applique la couleur à chacun des clusters
            fig = go.Figure(data=data) # on regroupe tous les graphiques en bar créé par la boucle
            fig.update_xaxes(tickangle=-90) #Pour mettre les labels x à la verticale
            fig.update_layout(title = "Nombre de Sélection moyen<br>par catégorie", #Titre du graphique
                              yaxis_title = "Nombre de Sélection moyen", #Label y
                              legend_title = "Cluster", #Titre du bloc légende
                              height = 550, #Hauteur du graphique (afin que les trois graphiques en bar de la page soient homogènes)
                              width = 400,
                              font = dict(size = 14)) #Pour augmenter la taille de la police
            st.plotly_chart(fig) #Pour afficher le graphique
        ##############GRAPHIQUE MARQUES DE BEAUTE PREFEREES:  
        with col2:
            df_brand = df_result[["access_brand","mass_brand","premium_brand","hdg_brand","prestige_brand","luxe_brand","bio_brand","cluster"]] #Créé un dataframe avec que les colonnes nécessaires       
            df_brand = df_brand.groupby("cluster").mean().reset_index() #Regroupe les informations par cluster (aggrégation : moyenne)
            categories=["access","mass","premium","hdg","prestige","luxe","bio"] #Créer une liste de label pour la légende
            couleur = ["gold","deeppink","orange","lemonchiffon"] #Créer la liste de couleur pour différencier les clusters
            #Pour chacun des clusters choisis (df_brand est créé à partir de df_result, donc les clusters non choisis sont déjà enlevés)
            data = []
            for cluster_i in range(len(df_brand["cluster"])): #Pour chacun des clusters dans les clusters séléctionnés
                liste = []
                for i in range(1,8): #Pour chacune des colonnes brand du df_brand
                    liste.append(df_brand.iloc[cluster_i,i]) #On ajoute à la liste les différentes moyennes corréspondant aux différentes marques pour chacun des clusters
                data.append(go.Bar(name=f'cluster {df_brand.iloc[cluster_i,0]}', x=categories, y=liste,marker_color = f"{couleur[cluster_i]}")) #On créer différents graphiques en bar, name : sert à identifier les différents clusters
            fig = go.Figure(data=data) # on regroupe tous les graphiques en bar créé par la boucle
            fig.update_xaxes(tickangle=-90) #Pour mettre les labels x à la verticale
            fig.update_layout(title = "Nombre de Sélection moyen<br>par Préférence de Marque de Beauté", #Titre du graphique
                              yaxis_title = "Nombre de Sélection moyen", #Label y
                              legend_title = "Cluster", #Titre du bloc légende
                              height = 425, #Hauteur du graphique (afin que les trois graphiques en bar de la page soient homogènes)
                              width = 400,
                              font = dict(size = 14)) #Pour augmenter la taille de la police
            st.plotly_chart(fig) #Pour afficher le graphique
        ##############GRAPHIQUE MARQUES DE MODE PREFEREES:     
        with col3:
            df_mode = df_result[["access_mode","mass_mode","premium_mode","hdg_mode","hdg_mode","prestige_mode","luxe_mode","vintage_mode","eco_responsable_mode","cluster"]] #Créé un dataframe avec que les colonnes nécessaires       
            df_mode = df_mode.groupby("cluster").mean().reset_index() #Regroupe les informations par cluster (aggrégation : moyenne)
            categories=["access","mass_mode","premium","hdg","hdg","prestige","luxe","vintage","eco_responsable"] #Créer une liste de label pour la légende
            couleur = ["gold","deeppink","orange","lemonchiffon"] #Créer la liste de couleur pour différencier les clusters
            #Pour chacun des clusters choisis (df_mode est créé à partir de df_result, donc les clusters non choisis sont déjà enlevés)
            data = []
            for cluster in range(len(df_mode["cluster"])): #Pour chacun des clusters dans les clusters séléctionnés
                liste = []
                for i in range(1,9): #Pour chacune des colonnes mode du df_mode
                    liste.append(df_mode.iloc[cluster,i]) #On ajoute à la liste les différentes moyennes corréspondant aux différentes marques pour chacun des clusters
                data.append(go.Bar(name=f'cluster {df_mode.iloc[cluster,0]}', x=categories, y=liste,marker_color = f"{couleur[cluster]}")) #On créer différents graphiques en bar, name : sert à identifier les différents clusters
            fig = go.Figure(data=data) # on regroupe tous les graphiques en bar créé par la boucle
            fig.update_xaxes(tickangle=-90) #Pour mettre les labels x à la verticale
            fig.update_layout(title = "Nombre de Sélection moyen<br>par Préférence de Marque de Mode", #Titre du graphique
                              yaxis_title = "Nombre de Sélection moyen", #Label y
                              legend_title = "Cluster", #Titre du bloc légende
                              width = 400,
                              font = dict(size = 14)) #Pour augmenter la taille de la police
            st.plotly_chart(fig) #Pour afficher le graphique
            
        #Ecris le titre 2 de la page : 
        st.title(f"Information sur les votes du cluster {a} : ")
        
        col1, col2 = st.columns(2)
        ##############GRAPHIQUE DES LIKE/DISLIKE CATEGORIE DE PRODUITS:  
        with col1:
            #Créer toutes les valeurs nécessaire au graphique : les moyennes du nombre de like et dislike par catégorie
            like_Naturel = df_result["like_Naturel"].sum()
            like_Synthetique = df_result["like_Synthetique"].sum()
            like_Ecolabel = df_result["like_Ecolabel"].sum()
            like_Vif = df_result["like_vif"].sum()
            like_Neutre = df_result["like_neutre"].sum()
            dislike_Naturel = df_result["dislike_Naturel"].sum()
            dislike_Synthetique = df_result["dislike_Synthetique"].sum()
            dislike_Ecolabel = df_result["dislike_Ecolabel"].sum()
            dislike_Vif = df_result["dislike_vif"].sum()
            dislike_Neutre = df_result["dislike_neutre"].sum()
            #Créer la liste des valeurs avec les variables créées : (attention : pour les dislikes on ajoute un "-" afin que les valeurs soient négatives)
            vote = [like_Naturel,like_Synthetique,like_Ecolabel,like_Vif,like_Neutre,-dislike_Naturel,-dislike_Synthetique,-dislike_Ecolabel,-dislike_Vif,-dislike_Neutre]
            #Définie pour chacune des valeurs de vote si c'est like ou dislike afin de l'attribuer dans la légende :
            type_vote = ["Like","Like","Like","Like","Like","Dislike","Dislike","Dislike","Dislike","Dislike"]
            #Créer le dataframe pour associer chaques valeurs à son type Like/Dislike:
            df_vote = pd.DataFrame({"type_vote":type_vote,
                                    "vote":vote})
            fig = px.bar(x=["Naturel","Synthetique","Ecolabel","Vif","Neutre","Naturel","Synthetique","Ecolabel","Vif","Neutre"], #Label de chaque type de catégories attribuées aux produits votés
                        y=df_vote["vote"], #Valeurs des moyennes de vote
                        color = df_vote["type_vote"], #Pour mettre une couleur jaune aux Like et rose aux Dislike
                        color_discrete_map={'Like': 'gold','Dislike': 'deeppink'},
                        labels={"x": "critère ciblé", #On supprime le label de l'axe x car cela est déjà identifié par le type de catégories
                                "y": "Nombre de vote", #Label de l'axe y
                                "color":"Type de votes"}, #Titre du bloc de legende
                        title = "nombre de Like/Dislike d'articles ayant le critère ciblé") #Titre du graphique
            fig.update_layout(font = dict(size = 14),
                             width = 500) #Augmente la taille de la police
            st.plotly_chart(fig) #Pour afficher le graphique
            
        ##############GRAPHIQUE LIKE/DISLIKE DES PRIX:  
        with col2:
            #Créer toutes les valeurs nécessaire au graphique : les moyennes des prix des produits liké et disliké
            like_price = df_result["like_price"].mean() 
            dislike_price = df_result["dislike_price"].mean()
            #Créer la liste des valeurs avec les variables créées : (attention : pour les dislikes on ajoute un "-" afin que les valeurs soient négatives)
            vote = [like_price/100,-dislike_price/100] #On divise par 100 Pour afficher les prix en euros 
            #Définie pour chacune des valeurs de vote si c'est like ou dislike afin de l'attribuer dans la légende :
            type_vote = ["Like","Dislike"]
            #Créer le dataframe pour associer chaques valeurs à son type Like/Dislike:
            df_vote = pd.DataFrame({"type_vote":type_vote,
                                    "vote":vote})
            fig = px.bar(x=df_vote["vote"], #Label de chaque type de catégories attribuées aux produits votés
                        y=["Prix","Prix"], #Valeurs des moyennes de vote
                        color = df_vote["type_vote"], #Pour mettre une couleur jaune aux Like et rose aux Dislike
                        color_discrete_map={'Like': 'gold','Dislike': 'deeppink'},
                        labels={"x": "Prix moyen (€)", #Label de l'axe x
                                "y": "", #On supprime le label de l'axe y car cela est déjà identifié par le type de catégories
                                "color":"Type de vote"}, #Titre du bloc de legende
                        title = 'Prix moyen des produits Likés vs Dislikés', #Titre du graphique
                        width = 500,
                        height=250) #Hauteur du graphique pour qu'il soit pas trop large
            fig.update_layout(font = dict(size = 14)) #Augmente la taille de la police
            st.plotly_chart(fig) #Pour afficher le graphique
            
        ######################### GRAPHIQUE PERSONNALISABLE :
        st.title("Graphiques personnalisables :")
        df_perso=df_result.drop(columns="user id")
        measures = df_perso.columns
        col1,col2,col3,col4,col5 = st.columns(5)
        with col1:
            scatter_x_1 = st.selectbox("X axis:", measures)
        with col2:
            scatter_y_1 = st.selectbox("Y axis:", measures)
        with col4:
            scatter_x_2= st.selectbox("X axis :", measures)
        with col5:
            scatter_y_2 = st.selectbox("Y axis :", measures)
        col1,col2 = st.columns(2)
        with col1:
            fig = px.scatter(df_perso, 
                             x=scatter_x_1, 
                             y=scatter_y_1, 
                             title="Corrélation", 
                             color = "cluster",
                             color_discrete_sequence= px.colors.sequential.Plasma_r,
                            widht = 500)
            st.plotly_chart(fig)
        with col2:
            fig = px.scatter(df_perso, 
                             x=scatter_x_2, 
                             y=scatter_y_2, 
                             title="Corrélation", 
                             color = "cluster",
                             color_discrete_sequence= px.colors.sequential.Plasma_r,
                            width = 500)
            st.plotly_chart(fig)
        
        
        


        
            
            
        
        

            
            
        
        
        
        
        
