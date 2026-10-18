# Buildozer configuration for YouTube Streamer Android APK
# This file configures the build process for generating an APK/AAB

[app]

# Title of your application
title = YouTube Streamer

# Package name
package.name = youtubestreamer

# Package domain (for Play Store)
package.domain = com.youtubestreamer

# Source code location
source.dir = .

# Source code version control
source.scm_git =

# Version of your application
version = 1.0.0

# Version number (integer)
version.code = 1

# Version code (for Play Store)
version.name = 1.0.0

# Requirements (packages needed by your application)
requirements = python3,kivy,pyjnius,jnius,requests,certifi,urllib3,idna,charset-normalizer,certifi,yt-dlp

# Android API levels
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21

# Android permissions
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WAKE_LOCK,FOREGROUND_SERVICE,FOREGROUND_SERVICE_MEDIA_PLAYBACK

# Android entry point
android.entrypoint = org.kivy.android.PythonActivity

# Android app theme
android.apptheme = @android:style/Theme.Material.NoActionBar

# Android orientation (portrait, landscape, sensor)
android.orientation = sensor

# Android icon
android.icon = @drawable/icon

# Android splash screen
android.splash = @drawable/splash

# Android status bar color
android.statusbarcolor = #121212

# Python packaging options
python.packages = python3,kivy,pyjnius,jnius,requests,certifi,urllib3,idna,charset-normalizer,certifi,yt-dlp

# Python source directory (optional)
python.source_dir = .

# Preserving Python files
preserved_dirs = __pycache__

# Buildozer logging level
log_level = 2

# Enable GUI debugging
gui = 1

# Android private storage
android.private_storage = false

# Android hardware acceleration
android.hardware_acceleration = true

# Android camera permission (if needed)
# android.permissions = CAMERA,RECORD_AUDIO

# Android microphone permission (if needed)
# android.permissions = RECORD_AUDIO

# Android storage permission (if needed)
# android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# Android network security config
# android.network_security_config = @xml/network_security_config

# Android manifest placeholders
# android.manifest.placeholders = {android.hardware.camera="false"}

# Android gradle properties
# android.gradle_dependencies =

# Android exclude folders
# android.exclude =

# Android include folders
# android.include =

# Android prebuilt python
# android.prebuilt_python =

# Android build tools
# android.build_tools =

# Android sdk
# android.sdk =

# Android sdk path
# android.sdk.path =

# Android ndk path
# android.ndk.path =

# Android ndk version
# android.ndk.version =

# Android sdk version
# android.sdk.version =

# Android target
# android.target =

# Android extra tools
# android.extra_tools =

# Android extra frameworks
# android.extra_frameworks =

# Android extra permissions
# android.extra_permissions =

# Android extra imports
# android.extra_imports =

# Android extra sources
# android.extra_sources =

# Android extra resources
# android.extra_resources =

# Android extra assets
# android.extra_assets =

# Android extra data
# android.extra_data =

# Android extra libs
# android.extra_libs =

# Android extra modules
# android.extra_modules =

# Android extra packages
# android.extra_packages =

# Android extra services
# android.extra_services =

# Android extra receivers
# android.extra_receivers =

# Android extra providers
# android.extra_providers =

# Android extra activities
# android.extra_activities =

# Android extra intents
# android.extra_intents =

# Android extra filters
# android.extra_filters =

# Android extra categories
# android.extra_categories =

# Android extra actions
# android.extra_actions =

# Android extra types
# android.extra_types =

# Android extra schemes
# android.extra_schemes =

# Android extra host
# android.extra_host =

# Android extra port
# android.extra_port =

# Android extra path
# android.extra_path =

# Android extra query
# android.extra_query =

# Android extra fragment
# android.extra_fragment =

# Android extra authority
# android.extra_authority =

# Android extra segment
# android.extra_segment =

# Android extra id
# android.extra_id =

# Android extra label
# android.extra_label =

# Android extra description
# android.extra_description =

# Android extra summary
# android.extra_summary =

# Android extra enabled
# android.extra_enabled =

# Android extra exported
# android.extra_exported =

# Android extra process
# android.extra_process =

# Android extra theme
# android.extra_theme =

# Android extra config
# android.extra_config =

# Android extra name
# android.extra_name =

# Android extra value
# android.extra_value =

# Android extra type
# android.extra_type =

# Android extra format
# android.extra_format =

# Android extra min
# android.extra_min =

# Android extra max
# android.extra_max =

# Android extra step
# android.extra_step =

# Android extra orientation
# android.extra_orientation =

# Android extra screenDensity
# android.extra_screenDensity =

# Android extra screenWidth
# android.extra_screenWidth =

# Android extra screenHeight
# android.extra_screenHeight =

# Android extra screenLayout
# android.extra_screenLayout =

# Android extra uiOptions
# android.extra_uiOptions =

# Android extra windowSoftInputMode
# android.extra_windowSoftInputMode =

# Android extra hardwareAccelerated
# android.extra_hardwareAccelerated =

# Android extra theme
# android.extra_theme =

# Android extra configChanges
# android.extra_configChanges =

# Android extra launchMode
# android.extra_launchMode =

# Android extra screenOrientation
# android.extra_screenOrientation =

# Android extra taskAffinity
# android.extra_taskAffinity =

# Android extra allowTaskReparenting
# android.extra_allowTaskReparenting =

# Android extra alwaysRetainTaskState
# android.extra_alwaysRetainTaskState =

# Android extra clearTaskOnLaunch
# android.extra_clearTaskOnLaunch =

# Android extra finishOnTaskLaunch
# android.extra_finishOnTaskLaunch =

# Android extra excludeFromRecents
# android.extra_excludeFromRecents =

# Android extra launchTaskBehindTargetTask
# android.extra_launchTaskBehindTargetTask =

# Android extra launchTaskBehindSourceTask
# android.extra_launchTaskBehindSourceTask =

# Android extra permission
# android.extra_permission =

# Android extra protected
# android.extra_protected =

# Android extra protectionLevel
# android.extra_protectionLevel =

# Android extra sharedUserId
# android.extra_sharedUserId =

# Android extra sharedUserLabel
# android.extra_sharedUserLabel =

# Android extra versionCode
# android.extra_versionCode =

# Android extra versionName
# android.extra_versionName =

# Android extra installLocation
# android.extra_installLocation =

# Android extra largeHeap
# android.extra_largeHeap =

# Android extra networkSecurityConfig
# android.extra_networkSecurityConfig =

# Android extra usesCleartextTraffic
# android.extra_usesCleartextTraffic =

# Android extra debuggable
# android.extra_debuggable =

# Android extra testOnly
# android.extra_testOnly =

# Android extra extractNativeLibs
# android.extra_extractNativeLibs =

# Android extra fullBackupContent
# android.extra_fullBackupContent =

# Android extra restoreAnyVersion
# android.extra_restoreAnyVersion =

# Android extra allowBackup
# android.extra_allowBackup =

# Android extra enableOnBackInvokedCallback
# android.extra_enableOnBackInvokedCallback =

# Android extra appCategory
# android.extra_appCategory =

# Android extra appCategory
# android.extra_appCategory =

# Android extra appCategory
# android.extra_appCategory =

# Android extra appCategory
# android.extra_appCategory =

# Android extra appCategory
# android.extra_appCategory =

[buildozer]

# Buildozer version
version = 1.5.0

# Buildozer log level
log_level = 2

# Buildozer gui
gui = 1

# Buildozer target
# target = android

# Buildozer platform
# platform = android

# Buildozer android
# android =

# Buildozer python
# python =

# Buildozer kivy
# kivy =

# Buildozer requirements
# requirements =

# Buildozer source
# source =

# Buildozer package
# package =

# Buildozer version
# version =

# Buildozer title
# title =

# Buildozer dir
# dir =

# Buildozer spec
# spec =

# Buildozer config
# config =

# Buildozer build
# build =

# Buildozer deploy
# deploy =

# Buildozer run
# run =

# Buildozer serve
# serve =

# Buildozer reset
# reset =

# Buildozer help
# help =

# Buildozer version
# version =

# Buildozer debug
# debug =

# Buildozer release
# release =

# Buildozer sign
# sign =

# Buildozer release-sign
# release-sign =

# Buildozer release-sign-alias
# release-sign-alias =

# Buildozer release-sign-keypass
# release-sign-keypass =

# Buildozer release-sign-storepass
# release-sign-storepass =

# Buildozer release-sign-keystore
# release-sign-keystore =

# Buildozer release-sign-certfile
# release-sign-certfile =

# Buildozer release-sign-v1
# release-sign-v1 =

# Buildozer release-sign-v2
# release-sign-v2 =

# Buildozer release-sign-v3
# release-sign-v3 =

# Buildozer release-sign-apksigner
# release-sign-apksigner =

# Buildozer release-sign-jarsigner
# release-sign-jarsigner =

# Buildozer release-sign-openssl
# release-sign-openssl =

# Buildozer release-sign-keytool
# release-sign-keytool =

# Buildozer release-sign-java
# release-sign-java =

# Buildozer release-sign-jdk
# release-sign-jdk =

# Buildozer release-sign-jre
# release-sign-jre =

# Buildozer release-sign-brew
# release-sign-brew =

# Buildozer release-sign-apt
# release-sign-apt =

# Buildozer release-sign-yum
# release-sign-yum =

# Buildozer release-sign-zypper
# release-sign-zypper =

# Buildozer release-sign-pacman
# release-sign-pacman =

# Buildozer release-sign-conda
# release-sign-conda =

# Buildozer release-sign-mamba
# release-sign-mamba =

# Buildozer release-sign-pip
# release-sign-pip =

# Buildozer release-sign-npm
# release-sign-npm =

# Buildozer release-sign-cargo
# release-sign-cargo =

# Buildozer release-sign-go
# release-sign-go =

# Buildozer release-sign-ruby
# release-sign-ruby =

# Buildozer release-sign-php
# release-sign-php =

# Buildozer release-sign-perl
# release-sign-perl =

# Buildozer release-sign-python
# release-sign-python =

# Buildozer release-sign-node
# release-sign-node =

# Buildozer release-sign-deno
# release-sign-deno =

# Buildozer release-sign-bun
# release-sign-bun =

# Buildozer release-sign-yarn
# release-sign-yarn =

# Buildozer release-sign-pnpm
# release-sign-pnpm =

# Buildozer release-sign-bunx
# release-sign-bunx =

# Buildozer release-sign-npx
# release-sign-npx =

# Buildozer release-sign-yarnx
# release-sign-yarnx =

# Buildozer release-sign-pnpmx
# release-sign-pnpmx =

# Buildozer release-sign-bunx
# release-sign-bunx =

# Buildozer release-sign-npx
# release-sign-npx =

# Buildozer release-sign-yarnx
# release-sign-yarnx =

# Buildozer release-sign-pnpmx
# release-sign-pnpmx =
