const { createApp, onMounted, ref, reactive } = Vue;

createApp({
    setup() {
        const status = ref('offline');
        const peers = ref(0);
        const nodeId = ref('unknown');
        const metrics = reactive({
            cpu_usage: 0,
            memory_usage: 0,
            memory_used_mb: 0,
            memory_total_mb: 0,
            uptime: 0
        });
        const meshPeers = ref([]);
        const logEntries = ref([
            { time: new Date().toLocaleTimeString(), type: 'INFO', message: 'Dashboard initialized' },
            { time: new Date().toLocaleTimeString(), type: 'GOSSIP', message: 'Scanning for network neighbors...' }
        ]);

        let cpuChart = null;
        let memoryChart = null;

        const formatUptime = (seconds) => {
            const h = Math.floor(seconds / 3600);
            const m = Math.floor((seconds % 3600) / 60);
            const s = Math.floor(seconds % 60);
            return `${h}h ${m}m ${s}s`;
        };

        const updateCharts = () => {
            if (cpuChart) {
                cpuChart.data.datasets[0].data = [metrics.cpu_usage, 100 - metrics.cpu_usage];
                cpuChart.update();
            }
            if (memoryChart) {
                memoryChart.data.datasets[0].data = [metrics.memory_usage, 100 - metrics.memory_usage];
                memoryChart.update();
            }
        };

        const fetchStatus = async () => {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                status.value = data.status;
                peers.value = data.peers;
                nodeId.value = data.node_id;
                
                if (data.metrics) {
                    Object.assign(metrics, data.metrics);
                }

                if (data.peer_list) {
                    meshPeers.value = data.peer_list.map(p => ({
                        url: p,
                        status: 'online'
                    }));
                }

                updateCharts();
            } catch (error) {
                console.error('Failed to fetch node status:', error);
                status.value = 'offline';
            }
        };

        const initCharts = () => {
            const commonOptions = {
                cutout: '80%',
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false }, tooltip: { enabled: false } },
                elements: { arc: { borderWidth: 0 } }
            };

            const cpuCtx = document.getElementById('cpuChart').getContext('2d');
            cpuChart = new Chart(cpuCtx, {
                type: 'doughnut',
                data: {
                    datasets: [{
                        data: [0, 100],
                        backgroundColor: ['#4facfe', 'rgba(255, 255, 255, 0.05)'],
                    }]
                },
                options: commonOptions
            });

            const memCtx = document.getElementById('memoryChart').getContext('2d');
            memoryChart = new Chart(memCtx, {
                type: 'doughnut',
                data: {
                    datasets: [{
                        data: [0, 100],
                        backgroundColor: ['#00f2fe', 'rgba(255, 255, 255, 0.05)'],
                    }]
                },
                options: commonOptions
            });
        };

        onMounted(() => {
            initCharts();
            fetchStatus();
            setInterval(fetchStatus, 2000);
        });

        return {
            status,
            peers,
            nodeId,
            metrics,
            meshPeers,
            logEntries,
            formatUptime
        };
    }
}).mount('#app');
