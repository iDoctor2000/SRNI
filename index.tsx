// Inyectar configuración PWA y metaetiquetas para móviles
const injectPwaConfig = () => {
    const head = document.head;

    // Enlace al Manifest.json (Android/Chrome)
    if (!document.querySelector('link[rel="manifest"]')) {
        const manifestLink = document.createElement('link');
        manifestLink.rel = 'manifest';
        manifestLink.href = 'manifest.json';
        head.appendChild(manifestLink);
    }

    // Icono para Apple (iOS)
    if (!document.querySelector('link[rel="apple-touch-icon"]')) {
        const iconLink = document.createElement('link');
        iconLink.rel = 'apple-touch-icon';
        iconLink.href = 'IMG/SRNI.png';
        head.appendChild(iconLink);
    }

    // Título de la App en iOS (Debajo del icono)
    if (!document.querySelector('meta[name="apple-mobile-web-app-title"]')) {
        const titleMeta = document.createElement('meta');
        titleMeta.name = 'apple-mobile-web-app-title';
        titleMeta.content = 'SRNI';
        head.appendChild(titleMeta);
    }

    // Capacidad de App Web (iOS)
    if (!document.querySelector('meta[name="apple-mobile-web-app-capable"]')) {
        const capableMeta = document.createElement('meta');
        capableMeta.name = 'apple-mobile-web-app-capable';
        capableMeta.content = 'yes';
        head.appendChild(capableMeta);
    }

    // Estilo de barra de estado (iOS)
    if (!document.querySelector('meta[name="apple-mobile-web-app-status-bar-style"]')) {
        const statusMeta = document.createElement('meta');
        statusMeta.name = 'apple-mobile-web-app-status-bar-style';
        statusMeta.content = 'black-translucent';
        head.appendChild(statusMeta);
    }
};

injectPwaConfig();