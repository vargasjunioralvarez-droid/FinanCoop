# ProGuard rules for FinanCoop

# Keep Capacitor classes
-keep class com.capacitorjs.** { *; }
-keep class com.getcapacitor.** { *; }

# Keep WebView
-keep class android.webkit.** { *; }

# Keep JavaScript interfaces
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}

# Keep Vue/Vite generated files
-keep class **.R$* { *; }
-keep class **.R { *; }

# Remove logs in release
-assumenosideeffects class android.util.Log {
    public static boolean isLoggable(java.lang.String, int);
    public static int v(...);
    public static int i(...);
    public static int w(...);
    public static int d(...);
    public static int e(...);
}

# Optimize
-optimizationpasses 5
-dontusemixedcaseclassnames
-dontskipnonpubliclibraryclasses
-dontpreverify
-verbose