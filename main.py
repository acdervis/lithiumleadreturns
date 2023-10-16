from datetime import datetime
import altair as alt
import polars as pl
import streamlit as st

MAX_YR = 30
MAX_MO = MAX_YR * 12 + 1
TODAY = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
DOLLAR_TL = 1/28

col_left, col_mid, col_right = st.columns(3)


with col_left:
    st.header("Kurşun-Asit")
    lacid_price = st.number_input("Fiyat ($)",
                                  key='lacid_price',
                                  value=1400.00,
                                  min_value=0.01,
                                  help="Dolar cinsinden kurşun-asit batarya fiyatı",
                                  )
    lacid_lifespan = st.slider("Ömrü (sene)",
                               key='lacid_lifespan',
                               value=4,
                               min_value=1,
                               max_value=20,
                               step=1
                               )
    lacid_maintenance_interval = st.number_input("Bakım Periyodu",
                                                 key='lacid_maintenance_interval',
                                                 value=1.0,
                                                 min_value=0.1,
                                                 step=0.1,
                                                 format='%0.1f',
                                                 help="Senede kaç bakım yapılacağı",
                                                 )
    lacid_maintenance_cost = st.number_input("Bakım Masrafı (₺)",
                                             key='lacid_maintenance_cost',
                                             value=2000.00,
                                             min_value=0.01,
                                             help="Bakım başına TL(₺) gider"
                                             )
    lacid_waste_value = st.number_input("Hurda Değeri ($)",
                                        key='lacid_waste_value',
                                        value=150.00,
                                        min_value=0.01,
                                        )


with col_mid:
    st.header("Lityum")
    lithium_price = st.number_input("Fiyat ($)",
                                    key="lithium_price",
                                    value=1600.00,
                                    min_value=0.01,
                                    help="Dolar cinsinden lityum batarya fiyatı", 
                                    )
    lithium_lifespan = st.slider("Ömrü (sene)",
                                 key='lithium_lifespan',
                                 value=8,
                                 min_value=1,
                                 max_value=20,
                                 step=1
                                 )
    lithium_adv_factor = st.slider("Enerji Verimlilik Avantajı",
                                   key='lithium_electricity_advantage',
                                   value=-0.3,
                                   min_value=-0.99,
                                   max_value=0.0,
                                   help="Kurşun-Asit'e göre enerji tüketimi",
                                   )


with col_right:
    st.header("Diğer")
    elec_price = st.number_input("Elektrik Fiyatı (₺/kWh)",
                                 value=4.53,
                                 min_value=0.01,
                                 )
    elec_usage = st.number_input("Elektrik Tüketimi (kWh/ay)",
                                 value=80.0,
                                 min_value=0.1,
                                 step=0.1,
                                 format="%0.1f",
                                 help="Bir makinenin kurşun-asit akü ile ayda tükettiği elektrik (kWh)",
                                 )
    projection_time = st.slider("Projeksiyon Süresi (sene)",
                                value=10,
                                min_value=5,
                                max_value=30,
                                step=1,
                                )

future = TODAY.replace(year=TODAY.year + MAX_YR)
dr = pl.datetime_range(
    TODAY,
    future,
    '1mo',
    closed='both',
    eager=True,
)

electricity_costs = elec_price * DOLLAR_TL * elec_usage
lithium_purchase_costs = [lithium_price if n % (lithium_lifespan*12) == 0 else 0 for n in range(MAX_MO)]
lithium_electricity_costs = [electricity_costs * (1+lithium_adv_factor)] * MAX_MO
lacid_purchase_costs = [lacid_price if n % (lacid_lifespan*12) == 0 else 0 for n in range(MAX_MO)]
lacid_maintenance_costs = [lacid_maintenance_cost*DOLLAR_TL if n % (lacid_maintenance_interval*12) == 0 else 0 for n in range( MAX_MO)]
lacid_waste_costs = [(0-lacid_waste_value) if n % (lacid_lifespan*12) == 0 and n != 0 else 0 for n in range(MAX_MO)]
lacid_electricity_costs = [electricity_costs] * MAX_MO

df = pl.DataFrame({
    'date': dr,
    'lithium_purchase_costs': lithium_purchase_costs,
    'lithium_electricity_costs': lithium_electricity_costs,
    'lacid_purchase_costs': lacid_purchase_costs,
    'lacid_maintenance_costs': lacid_maintenance_costs,
    'lacid_waste_costs': lacid_waste_costs,
    'lacid_electricity_costs': lacid_electricity_costs,
})

df = df.with_columns(pl.sum_horizontal('lithium_purchase_costs', 'lithium_electricity_costs').cumsum().alias('lithium_costs'))
df = df.with_columns(pl.sum_horizontal('lacid_purchase_costs',
                                       'lacid_maintenance_costs',
                                       'lacid_waste_costs',
                                       'lacid_electricity_costs',
                                       ).cumsum().alias('lacid_costs'))

molten = df.melt('date', value_vars=['lithium_costs', 'lacid_costs'])

p_select = alt.selection_multi(on='mouseover', nearest=True)
st.altair_chart(
    alt.Chart(molten.filter(pl.col('date') < TODAY.replace(year=TODAY.year + projection_time))).mark_line().encode(
        x='date',
        y='value',
        color='variable',
    ).add_params(
        p_select
    ).interactive(),
    theme='streamlit',
    use_container_width=True
)
