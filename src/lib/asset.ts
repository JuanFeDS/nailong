declare const __ASSET_VERSION__: string

// Las imágenes de public/ conservan su nombre al regenerarlas; la versión del despliegue
// en la URL evita que los celulares sigan mostrando la copia vieja guardada en caché.
export const asset = (path: string) =>
  `${import.meta.env.BASE_URL}${path}${/\.(png|jpe?g|webp|gif)$/.test(path) ? `?v=${__ASSET_VERSION__}` : ''}`
