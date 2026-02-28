# Functional Requirements - Ingestion and Retrieval

## FR-01 Unified Ingestion Layer
The system must ingest from:
- Unstructured: PDF contracts and bill of lading from S3 and SharePoint.
- Structured: Shipment logs from SAP and Oracle.
- Streaming: IoT streams via Kafka/Flink.
- External APIs: Port congestion and weather forecasts.
- Database calls from operational systems.

## FR-02 Retrieval Capability
The assistant must answer queries about:
- Shipment delays
- Vendor contracts
- Real-time IoT sensor state

## FR-03 Multimodal Query Support
The assistant must support retrieval over:
- Text and documents
- Tables from Excel/PDF
- Images (warehouse/IoT)

## FR-04 Filtered Retrieval
Users must be able to retrieve using metadata filters, including:
- `source_type`
- Time windows (`timestamp`)
- Domain filters (for example, report period or source format)
