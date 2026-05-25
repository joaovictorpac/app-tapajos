import ee
import geemap
import streamlit as st

# ==============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA (STREAMLIT)
# ==============================================================================
# Define que o site ocupará a tela inteira
st.set_page_config(page_title="Monitoramento Tapajós", layout="wide")

# Construção do Painel Lateral (Substitui o antigo ui.Panel)
st.sidebar.title("Avanço do Garimpo (Tapajós)")

st.sidebar.info("↔️ **Dica:** Arraste a barra central do mapa para comparar as datas.")

st.sidebar.markdown("""
A bacia do Tapajós tem sofrido intensas transformações. Observe como as cicatrizes de desmatamento associadas à mineração avançaram em direção à floresta.

### 👁️ Como ler a imagem (Falsa Cor)
* 🟢 **Verde:** Vegetação preservada.
* 🔴 **Vermelho intenso:** Solo exposto, desmatamento e mineração ativa.
""")

# ==============================================================================
# 2. INICIALIZAÇÃO DO EARTH ENGINE
# ==============================================================================
# O @st.cache_resource garante que o site não faça login no Google a cada clique
@st.cache_resource
def iniciar_ee():
    # Substitua pelo ID do seu projeto do Google Cloud
    ee.Initialize(project='seu-projeto-id') 

iniciar_ee()

# ==============================================================================
# 3. PROCESSAMENTO ESPACIAL (GEEMAP / GEE)
# ==============================================================================
ponto_central = ee.Geometry.Point([-56.88, -6.15])
geometry = ponto_central.buffer(15000).bounds()

def maskS2clouds(image):
    scl = image.select('SCL')
    mask = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10))
    return image.updateMask(mask).divide(10000)

s2_2019 = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
           .filterBounds(geometry)
           .filterDate('2019-07-01', '2019-11-30')
           .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
           .map(maskS2clouds).median().clip(geometry))

s2_2025 = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
           .filterBounds(geometry)
           .filterDate('2025-07-01', '2025-11-30')
           .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
           .map(maskS2clouds).median().clip(geometry))

# ==============================================================================
# 4. CONSTRUÇÃO DO MAPA INTERATIVO E LEGENDA
# ==============================================================================
# Cria a tela do mapa
Map = geemap.Map(center=[-6.15, -56.88], zoom=12)

vis_params = {'bands': ['B11', 'B8', 'B3'], 'min': 0.0, 'max': 0.35}

camada_2019 = geemap.ee_tile_layer(s2_2019, vis_params, '2019')
camada_2025 = geemap.ee_tile_layer(s2_2025, vis_params, '2025')

# Aplica o Split Panel
Map.split_map(left_layer=camada_2019, right_layer=camada_2025)

# Adiciona a legenda flutuante diretamente no mapa do geemap
dicionario_legenda = {
    'Vegetação Preservada': '27ae60',
    'Desmatamento / Garimpo': 'e74c3c'
}
Map.add_legend(title="Legenda Óptica", legend_dict=dicionario_legenda, position='bottomleft')

# ==============================================================================
# 5. RENDERIZAÇÃO FINAL
# ==============================================================================
# Envia o mapa pronto para ser exibido na página do Streamlit
Map.to_streamlit(height=700)