import { runKMeans, runDBSCAN } from './api.js';
import { initPlot, drawPoints, drawStep, convertClickToPoint } from './plot.js';

const { createApp, ref, onMounted, watch } = Vue;

const app = createApp({
    setup() {
        // State
        const algorithm = ref('kmeans');
        const k = ref(3);
        const eps = ref(1.0);
        const minPts = ref(3);
        const points = ref([]);
        const history = ref([]);
        const currentStep = ref(0);
        const isRunning = ref(false);

        // Actions
        const handleCanvasClick = (event) => {
            if (history.value.length > 0) return;
            const point = convertClickToPoint(event);
            if (point) {
                points.value.push(point);
                drawPoints(points.value);
            }
        };

        const runAlgorithm = async () => {
            isRunning.value = true;
            try {
                let data;
                if (algorithm.value === 'kmeans') {
                    data = await runKMeans(points.value, k.value);
                } else {
                    data = await runDBSCAN(points.value, parseFloat(eps.value), minPts.value);
                }

                if (data.success) {
                    history.value = data.history;
                    currentStep.value = 0;
                    drawStep(points.value, history.value[0]);
                } else {
                    alert('Error: ' + data.error);
                }
            } catch (e) {
                console.error(e);
                alert('Server error');
            } finally {
                isRunning.value = false;
            }
        };

        const clearPoints = () => {
            points.value = [];
            history.value = [];
            currentStep.value = 0;
            initPlot();
        };

        // Navigation
        const nextStep = () => { if (currentStep.value < history.value.length - 1) currentStep.value++; };
        const prevStep = () => { if (currentStep.value > 0) currentStep.value--; };
        const setStep = (val) => { currentStep.value = val; };

        // Watchers
        watch(currentStep, (newVal) => { 
            if (history.value.length > 0) drawStep(points.value, history.value[newVal]); 
        });
        watch(algorithm, () => { clearPoints(); });

        onMounted(() => {
            setTimeout(initPlot, 100);
        });

        return {
            algorithm, k, eps, minPts, points, history, currentStep, isRunning,
            runAlgorithm, nextStep, prevStep, setStep, clearPoints, handleCanvasClick
        };
    }
});

app.mount('#app');
