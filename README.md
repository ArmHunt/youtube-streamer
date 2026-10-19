# YouTube Streamer APK

**Build en la nube con GitHub Actions + Buildozer + Kivy**

## Cómo compilar el APK

### Opción 1: GitHub Actions (recomendado)

1. Ve a la pestaña **Actions** de tu repositorio
2. Click en **"Build YouTube Streamer APK"**
3. Selecciona **"Run workflow"** → elige `debug` o `release`
4. Espera ~20-30 minutos
5. Descarga el APK del artifact generado

### Opción 2: Build local (avanzado)

```bash
# Instalar dependencias
pip install buildozer cython kivy[android]

# Configurar SDK/NDK
sudo apt install openjdk-17-jdk

# Construir APK
buildozer android debug
```

## Arquitectura

- **UI:** Kivy (framework Python para móvil)
- **Backend:** yt-dlp (extracción de streams reales)
- **Paquete:** Buildozer → APK/AAB
- **Funciones premium:**
  - Búsqueda de YouTube
  - Reproducción con streams reales
  - Picture-in-Picture
  - Audio en segundo plano
  - Sin publicidad

## Flujo de build

```
GitHub Actions (ubuntu-latest)
  ├── Python 3.11
  ├── pip install buildozer cython
  ├── Descarga SDK/NDK/Android
  ├── buildozer android debug
  └── Artifact: youtube-streamer.apk (~50-100MB)
```
