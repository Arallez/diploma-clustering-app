import { runKMeans, runDBSCAN, runForel, runAgglomerative, generatePreset } from './api.js?v=4.0';
import { initPlot, drawPoints, drawStep, convertClickToPoint } from './plot.js?v=4.0';

const { createApp, ref, onMounted, watch } = Vue;

const app = createApp({
    setup() {
        // State
        const algorithm = ref('kmeans');
        const k = ref(3);
        const eps = ref(1.0);
        const minPts = ref(3);
        const radius = ref(1.0); // FOREL radius
        const points = ref([]);
        const history = ref([]);
        const currentStep = ref(0);
        const isRunning = ref(false);
        const selectedPreset = ref('');

        // Actions
        const handleCanvasClick = (event) => {
            if (history.value.length > 0) return;
            const point = convertClickToPoint(event);
            if (point) {
                points.value.push(point);
                drawPoints(points.value);
            }
        };

        const loadPreset = async () => {
            if (!selectedPreset.value) return;
            isRunning.value = true;
            try {
                const data = await generatePreset(selectedPreset.value, 100);
                if (data.success) {
                    points.value = data.points;
                    history.value = [];
                    currentStep.value = 0;
                    drawPoints(points.value);
                } else {
                    alert('Error loading preset: ' + data.error);
                }
            } catch (e) {
                console.error(e);
                alert('Server error');
            } finally {
                isRunning.value = false;
            }
        };

        const runAlgorithm = async () => {
            isRunning.value = true;
            try {
                let data;
                if (algorithm.value === 'kmeans') {
                    data = await runKMeans(points.value, k.value);
                } else if (algorithm.value === 'dbscan') {
                    data = await runDBSCAN(points.value, parseFloat(eps.value), minPts.value);
                } else if (algorithm.value === 'forel') {
                    data = await runForel(points.value, parseFloat(radius.value));
                } else if (algorithm.value === 'agglomerative') {
                    data = await runAgglomerative(points.value, k.value);
                }

                if (data && data.success) {
                    history.value = data.history;
                    currentStep.value = 0;
                    drawStep(points.value, history.value[0]);
                } else {
                    alert('Error: ' + (data ? data.error : 'Unknown error'));
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
            selectedPreset.value = '';
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
        watch(selectedPreset, () => { if (selectedPreset.value) loadPreset(); });

        onMounted(() => {
            setTimeout(initPlot, 100);
        });

        return {
            algorithm, k, eps, minPts, radius, points, history, currentStep, isRunning,
            selectedPreset, loadPreset,
            runAlgorithm, nextStep, prevStep, setStep, clearPoints, handleCanvasClick
        };
    }
});

app.mount('#app');
