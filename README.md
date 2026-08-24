# Gobierno en claro · Colombia

Aplicación ciudadana para explorar la estructura del Ejecutivo colombiano, sus responsables, entidades, territorio y agenda legislativa.

## Requisitos

- Node.js 22.13 o posterior
- pnpm

## Ejecutar localmente

```bash
pnpm install
pnpm dev
```

Luego abre la dirección local que aparece en la terminal.

## Comprobar el proyecto

```bash
pnpm lint
pnpm build
```

## Subir a GitHub

1. Crea un repositorio vacío en GitHub.
2. Sube todo el contenido de esta carpeta, incluidos los archivos que comienzan con punto.
3. No subas `node_modules`, `dist` ni otras carpetas generadas; ya están excluidas mediante `.gitignore`.

## Estructura principal

- `app/page.tsx`: interfaz y comportamiento de la aplicación.
- `app/data.ts`: información institucional utilizada por la aplicación.
- `app/globals.css`: diseño visual y estilos adaptables.
- `public/`: ícono e imagen para compartir en redes.
- `package.json`: dependencias y comandos del proyecto.

## Publicación

Este paquete conserva la configuración original usada para desarrollar la aplicación en OpenAI Sites. Guardarlo en GitHub funciona de inmediato como repositorio de código. Publicarlo mediante GitHub Pages requiere una adaptación adicional del proceso de compilación y de las rutas del repositorio.

## Vigilancia de fuentes oficiales

La segunda fase ejecuta diariamente el flujo `Vigilar fuentes oficiales` a las 06:15 de Colombia. Revisa fuentes oficiales de Presidencia y Senado y compara su contenido con la revisión anterior.

Cuando detecta un cambio o una fuente deja de responder, abre una alerta en GitHub Issues para revisión editorial. El monitor nunca modifica automáticamente el gabinete, la agenda legislativa ni el sitio publicado.

También puede ejecutarse manualmente desde **Actions → Vigilar fuentes oficiales → Run workflow**.
