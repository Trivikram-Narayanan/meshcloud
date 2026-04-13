# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial open source release of MeshCloud
- Distributed peer-to-peer file storage system
- Chunked file storage with deduplication
- BitTorrent-style replication across mesh network
- Automatic peer discovery via UDP broadcast
- Health monitoring and retry mechanisms
- RESTful API with FastAPI
- Command-line interface
- File watcher for automatic uploads
- SQLite database backend
- Comprehensive documentation

### Changed
- Migrated from proof-of-concept to production-ready codebase
- Improved error handling and logging
- Added proper dependency management
- Enhanced security with TLS support

### Technical Details
- Python 3.8+ compatibility
- FastAPI framework for API
- SQLite for data persistence
- SHA256 for file integrity
- 4MB chunk size for optimal performance

## [0.1.0] - 2024-01-XX

### Added
- Basic file upload and download functionality
- Peer-to-peer replication
- Chunked file transfer
- Database schema for file tracking
- Simple web dashboard
- CLI tool for basic operations

### Known Issues
- Limited error handling
- No authentication/authorization
- SQLite only (not suitable for multi-node)
- Basic testing coverage
- Self-signed certificates required