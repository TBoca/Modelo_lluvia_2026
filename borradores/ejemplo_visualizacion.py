"""
Script de ejemplo para visualizar datos descargados
Muestra cómo trabajar con los datos de NASA POWER
"""

import pandas as pd
import matplotlib.pyplot as plt

# Leer datos descargados
print("Leyendo datos de NASA POWER...")
df = pd.read_csv('nasa_power_pergamino_2023.csv', index_col=0, parse_dates=True)

print(f"\nDatos cargados: {len(df)} registros")
print(f"Período: {df.index[0]} a {df.index[-1]}")
print("\nColumnas disponibles:")
print(df.columns.tolist())

# Estadísticas básicas
print("\n" + "="*60)
print("ESTADÍSTICAS DESCRIPTIVAS - ENERO 2023")
print("="*60)
print(df.describe())

# Precipitación total
precip_total = df['PRECTOTCORR'].sum()
print(f"\n📊 Precipitación total enero 2023: {precip_total:.2f} mm")

# Temperaturas promedio
temp_media = df['T2M'].mean()
temp_max_abs = df['T2M_MAX'].max()
temp_min_abs = df['T2M_MIN'].min()

print(f"🌡️  Temperatura media: {temp_media:.2f}°C")
print(f"🔥 Temperatura máxima absoluta: {temp_max_abs:.2f}°C")
print(f"❄️  Temperatura mínima absoluta: {temp_min_abs:.2f}°C")

# Días con lluvia
dias_lluvia = (df['PRECTOTCORR'] > 0).sum()
print(f"🌧️  Días con precipitación: {dias_lluvia} de {len(df)} días")

# Crear visualización
print("\n📈 Generando gráficos...")

fig, axes = plt.subplots(2, 1, figsize=(12, 8))

# Gráfico 1: Precipitación
axes[0].bar(df.index, df['PRECTOTCORR'], color='steelblue', alpha=0.7)
axes[0].set_title('Precipitación Diaria - Pergamino, Enero 2023', fontsize=14, fontweight='bold')
axes[0].set_ylabel('Precipitación (mm/día)', fontsize=11)
axes[0].grid(True, alpha=0.3)
axes[0].set_xlim(df.index[0], df.index[-1])

# Gráfico 2: Temperaturas
axes[1].plot(df.index, df['T2M_MAX'], 'r-', label='Temperatura Máxima', linewidth=2)
axes[1].plot(df.index, df['T2M'], 'k-', label='Temperatura Media', linewidth=2)
axes[1].plot(df.index, df['T2M_MIN'], 'b-', label='Temperatura Mínima', linewidth=2)
axes[1].fill_between(df.index, df['T2M_MIN'], df['T2M_MAX'], alpha=0.2, color='gray')
axes[1].set_title('Temperaturas - Pergamino, Enero 2023', fontsize=14, fontweight='bold')
axes[1].set_ylabel('Temperatura (°C)', fontsize=11)
axes[1].set_xlabel('Fecha', fontsize=11)
axes[1].legend(loc='best')
axes[1].grid(True, alpha=0.3)
axes[1].set_xlim(df.index[0], df.index[-1])

plt.tight_layout()
plt.savefig('visualizacion_datos_pergamino.png', dpi=150, bbox_inches='tight')
print("✓ Gráfico guardado: visualizacion_datos_pergamino.png")

plt.show()

print("\n" + "="*60)
print("ANÁLISIS COMPLETADO")
print("="*60)
