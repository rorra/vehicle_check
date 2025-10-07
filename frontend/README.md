# Vehicle Check Frontend

Frontend de React para el sistema de inspección vehicular

## Tecnologías

- **React 19** con hooks
- **Vite 7** como build tool y dev server
- **React Router 7** para navegación
- **Axios** para consumir la API
- **Chakra UI** para estilos y componentes

## Instalación

1. **Instalar dependencias:**
   ```bash
   npm install
   ```

2. **Configurar variables de entorno:**

   El archivo `.env` ya está configurado con:
   ```
   VITE_API_BASE_URL=http://localhost:8000/api/v1
   ```

## Desarrollo

**Iniciar servidor de desarrollo:**
```bash
npm run dev
```

La aplicación estará disponible en `http://localhost:3000`

**Otros comandos:**
```bash
npm run build         # Compilar para producción
npm run preview       # Vista previa de la build de producción
npm run lint          # Ejecutar ESLint
npm test              # Ejecutar tests
npm run test:ui       # Ejecutar tests con interfaz gráfica
npm run test:coverage # Ejecutar tests con reporte de cobertura
```

## Testing

El proyecto utiliza **Vitest** y **React Testing Library** para pruebas unitarias.

**Ejecutar todos los tests:**
```bash
npm test
```
