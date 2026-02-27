# 🚀 - Advanced Industrial ERP Middleware Ecosystem

## 📺 Functional Evidence & Technical Operation
Click the button below to witness the system's real-time interaction with the Firebird SQL engine, showcasing FIFO costing, multithreaded notifications, and automated industrial reporting:

[![Watch System Demo](https://img.shields.io/badge/🎥_WATCH_SYSTEM_DEMO-MARETO_ERP_CORE-blue?style=for-the-badge&logo=googledrive)](https://drive.google.com/file/d/1S98KC4rGDMU8IcNMaLUM7H3vFEvp-VV2/view?usp=sharing)

> **Deployment Record:** `2026-02-27 13-22-56.mkv` | **Environment:** Industrial Production | **Target ERP:** Microsip 2026

---

## 📝 English Documentation: System Architecture & Design

### 🏛️ Industrial Executive Summary
This ecosystem represents a state-of-the-art **Industrial Middleware** designed to synchronize physical manufacturing floor operations with high-level financial planning (ERP). By eliminating the traditional lag between material consumption and accounting records, this solution ensures 100% data integrity, cost transparency, and operational scalability.

### 🛠️ Core Engineering Pillars

#### 1. Automated Layer-Based Costing Engine (FIFO/PEPS)
The system implements a sophisticated SQL-based valuation engine. Instead of simple unit subtraction, it performs deep queries into the **CAPAS_COSTOS** and **SALDOS_IN** tables to:
* **Trace Purchase Layers:** Identify exact acquisition prices for every material unit.
* **Accounting Precision:** Execute `GEN_ID` protocols and transactional `Commit/Rollback` sequences to maintain atomic database integrity.

#### 2. Multithreaded Communication Hub (Telegram API)
Designed for high-concurrency environments, the system manages an asynchronous notification bot.
* **Performance:** Utilizing Python's `threading` library, the bot operates in a non-blocking background process, ensuring the User Interface remains responsive during heavy data transmissions.
* **Instant Transparency:** Real-time alerts for supply chain milestones, critical stock levels, and quality incidents.

#### 3. Engineering Quality Control & Damage Assessment
A specialized module for industrial "Incident Management."
* **Surface Area Algorithms:** Calculates financial loss based on affected dimensions (cm²) for wood boards and specialized glass.
* **ERP-Linkage:** Directly connects current market prices from the ERP to the damage report, generating auditable PDF documents with legal disclaimers via the **ReportLab** engine.

### 📂 Repository Management
* **`CODE EN-SP/`**: Full implementation of the middleware core, ERP bridges, and UI modules, fully documented for international standard review.

---

## 📝 Documentación en Español: Arquitectura y Diseño de Sistema

### 🏛️ Resumen Ejecutivo Industrial
Este ecosistema representa un **Middleware Industrial** de última generación, diseñado para sincronizar las operaciones físicas de la planta con la planeación financiera de alto nivel (ERP). Al eliminar el retraso tradicional entre el consumo de material y el registro contable, esta solución garantiza el 100% de integridad de datos, transparencia de costos y escalabilidad operativa.

### 🛠️ Pilares de Ingeniería Core

#### 1. Motor de Costeo por Capas Automatizado (PEPS/FIFO)
El sistema implementa un motor de valoración basado en lógica SQL avanzada. En lugar de una simple resta de unidades, realiza consultas profundas en las tablas **CAPAS_COSTOS** y **SALDOS_IN** para:
* **Trazabilidad de Capas:** Identificar precios de adquisición exactos para cada unidad de material.
* **Precisión Contable:** Ejecutar protocolos `GEN_ID` y secuencias transaccionales `Commit/Rollback` para mantener la integridad atómica de la base de datos.

#### 2. Hub de Comunicación Multihilo (Telegram API)
Diseñado para entornos de alta concurrencia, el sistema gestiona un bot de notificaciones asíncronas.
* **Rendimiento:** Utilizando la librería `threading`, el bot opera en un proceso de fondo no bloqueante, asegurando que la interfaz de usuario se mantenga fluida durante transmisiones de datos pesadas.
* **Transparencia Instantánea:** Alertas en tiempo real sobre hitos de la cadena de suministro, niveles críticos de stock e incidentes de calidad.

#### 3. Control de Calidad e Ingeniería de Daños
Módulo especializado para la "Gestión de Incidentes" industriales.
* **Algoritmos de Superficie:** Calcula la pérdida financiera basada en dimensiones afectadas (cm²) para tableros y cristales especializados.
* **Vinculación ERP:** Conecta directamente los precios de adquisición actuales del ERP con el reporte de daños, generando documentos PDF auditables con cláusulas legales de responsabilidad mediante el motor **ReportLab**.

### 📂 Gestión de Repositorio
* **`CODE EN-SP/`**: Implementación completa del núcleo del middleware, puentes ERP y módulos de interfaz, totalmente documentados para implementación local.

---

**Author:** Ares Casale Marentis | **Year:** 2026




