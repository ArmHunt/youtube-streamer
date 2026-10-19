[app]

# Título de la aplicación
title = YouTube Streamer

# Nombre del paquete
package.name = youtubestreamer

# Dominio del paquete
package.domain = com.youtubestreamer

# Versión
version = 1.0.0
version.code = 1
version.name = 1.0.0

# Directorio de código fuente
source.dir = .

# Requisitos Python + dependencias
# Kivy para UI, yt-dlp para streams reales, dependencias de red
requirements = python3,kivy,pyjnius,requests,certifi,urllib3,idna,charset-normalizer,yt-dlp

# Nivel mínimo de Android API
android.api = 33
android.minapi = 21

# NDK version compatible con Android 33
android.ndk = 25b
android.ndk.api = 21

# Permisos de Android
# INTERNET: necesario para yt-dlp (stream de YouTube)
# ACCESS_NETWORK_STATE: verificar conexión
# WAKE_LOCK: mantener pantalla activa al reproducir
# FOREGROUND_SERVICE: audio en segundo plano / PiP
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WAKE_LOCK,FOREGROUND_SERVICE,FOREGROUND_SERVICE_MEDIA_PLAYBACK

# Orientación
android.orientation = sensor

# Tema de la app
android.apptheme = @android:style/Theme.Material.NoActionBar

# Color de la barra de estado
android.statusbarcolor = #121212

# Entrypoint de Kivy (por defecto, no tocar)
android.entrypoint = org.kivy.android.PythonActivity

# Logging
log_level = 2
