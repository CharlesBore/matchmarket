from requests.api import post
import streamlit as st
import pandas as pd
import folium
import json
import requests
import numpy as np
from streamlit_folium import folium_static

table = st.sidebar.checkbox("Afficher le Tableau de données ")
page = st.sidebar.radio("Page",("Graphique","Cluster"))
if page == "Graphique":
    type_graphique = st.selectbox("",("Carte de France","Carte par Département"))
    if type_graphique =="Carte de France":
        
        link = "https://raw.githubusercontent.com/FlorianMimolle/matchmarket/main/Streamlit/Departement.csv"
        df = pd.read_csv(link)
        df["Département"] = df["Département"].astype(str)
        df["Département"] = df["Département"].apply(lambda x : "0"+x if len(x)==1 else x)

        if table:
            st.write("Tableau de données : ")
            df
            
        state_geo = json.loads(requests.get("https://france-geojson.gregoiredavid.fr/repo/departements.geojson").text)

        for idx in range(len(state_geo["features"])):
            for index in range(len(df)):
                if str(state_geo["features"][idx]['properties']['code'])==str(df.iloc[index,0]):
                    state_geo["features"][idx]['properties']['nb_Client']= \
                    int(df['nb_Client'][index])
                    state_geo["features"][idx]['properties']['Âge'] = \
                    round(df['Âge'][index],2)
                    state_geo["features"][idx]['properties']['Urbain'] = \
                    str(round(100*df['Urbain'][index],2)) + " %"
                    state_geo["features"][idx]['properties']['%Like'] = \
                    str(round(df['%Like'][index],2))+" %"

        

        dicts = {"Nombre de Praedicters":'nb_Client',
                "Âge moyen": 'Âge',
                "Pourcentage de Preadicters venant du milieu Urbain": 'Urbain',
                "Pourcentage de Like": '%Like'}
        select_data = st.radio("",
        ("Nombre de Praedicters", "Âge moyen","Pourcentage de Preadicters venant du milieu Urbain",'Pourcentage de Like'))

        if select_data == "Pourcentage de Like":
            couleur = "RdYlGn"
        else:
            couleur = "RdPu"
        m = folium.Map(tiles="cartodb positron", 
                    location=[47, 2], 
                    zoom_start=6,)

        maps= folium.Choropleth(geo_data = state_geo,
                                data = df,
                                columns=['Département',dicts[select_data]],
                                key_on='properties.code',
                                fill_color=couleur,
                                fill_opacity=0.8,
                                line_opacity=0.2,
                                legend_name=dicts[select_data]
                                ).add_to(m)
        maps.geojson.add_child(folium.features.GeoJsonTooltip
                                        (aliases=["Département","n° Département",select_data],
                                        fields=["nom","code",dicts[select_data]],
                                        labels=True))

        folium_static(m)
        
    if type_graphique =="Carte par Département":
        link = "https://github.com/FlorianMimolle/matchmarket/raw/main/Streamlit/Postal_df.csv"
        df = pd.read_csv(link)
        df["Département"] = df["Département"].astype(str)
        df["Département"] = df["Département"].apply(lambda x : "0"+x if len(x)==1 else x)
        
        Département = st.selectbox('Quel numéro de département souhaitez-vous ? ', tuple(sorted(df["Département"].unique())))

        postal_df = df[df["Département"] == Département][["zipcode","user id","action_fact","Coordonnées","Age"]]
        postal_df = postal_df.groupby("zipcode").agg({"user id" : ["nunique"],
                                                    "action_fact":[lambda x : round(100-(x.mean()*100),2)],
                                                    "Coordonnées" : ["first"],
                                                    "Age":["mean"]
                                                    })
        postal_df = postal_df.reset_index()
        postal_df.columns = ["zipcode","nb_Personne","action_fact","Coordonnées","Age"]
        postal_df["color"] = postal_df["action_fact"].apply(lambda x : "#f24343" if x < 30 
                                                            else "#FFCF00" if x < 70
                                                            else "#27d830")
        postal_df = postal_df[postal_df["Coordonnées"].isnull() == False]
        postal_df["Coordonnées"] = postal_df["Coordonnées"].apply(lambda x : x.replace("[",""))
        postal_df["Coordonnées"] = postal_df["Coordonnées"].apply(lambda x : x.replace("]",""))
        postal_df["Coordonnées"] = postal_df["Coordonnées"].apply(lambda x : x.replace("'",""))
        postal_df["Coordonnées"] = postal_df["Coordonnées"].apply(lambda x : x.split(","))
        postal_df["lon"] = postal_df["Coordonnées"].apply(lambda x : x[0])
        postal_df["lat"] = postal_df["Coordonnées"].apply(lambda x : x[1])
        lon_mean = postal_df["lon"].astype(float).mean()
        lat_mean = postal_df["lat"].astype(float).mean()
        
        if table:
            postal_df
            
        m = folium.Map(location=[lon_mean, lat_mean], 
                       zoom_start=8, 
                       tiles='cartodb positron')

        for index in range(0,len(postal_df)):
            texte = f"<p>{postal_df.iloc[index,0]}<br /> \
            nb de Preadicters : {str(postal_df.iloc[index,1])}<br/> \
            nb de Like : {str(round(postal_df.iloc[index,2],2))+ ' %'}<br/> \
            moyenne d'âge : {str(round(postal_df.iloc[index,4],2))}</p>" 
                
            folium.Marker(location = postal_df.iloc[index,3],
                          popup = folium.Popup(texte,
                                               max_width=450),
                          icon=folium.Icon(color = "lightgray",
                                           icon_color=postal_df.iloc[index,5],
                                           icon = "user")
                          ).add_to(m)
                
        choropleth = folium.Choropleth(geo_data="https://france-geojson.gregoiredavid.fr/repo/departements.geojson",
                                       name="choropleth",
                                       fill_color="#FFCF00",
                                       fill_opacity=0.1
                                       ).add_to(m)

        # add labels indicating the name of the community
        style_function = "font-size: 10px"
        choropleth.geojson.add_child(folium.features.GeoJsonTooltip(['nom']+["code"],
                                                                    style=style_function,
                                                                    labels=False)
                                     )
        folium_static(m)
