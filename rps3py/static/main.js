document.addEventListener('DOMContentLoaded', function() {
    const manualBtn = document.getElementById('manualBtn');
    const randomBtn = document.getElementById('randomBtn');
    const manualInput = document.getElementById('manualInput');
    const sortBtn = document.getElementById('sortBtn');
    const results = document.getElementById('results');

    manualBtn.addEventListener('click', () => {
        manualInput.style.display = 'block';
        document.getElementById('arrayInput').focus();
    });

    randomBtn.addEventListener('click', () => {
        sortArray('random');
    });

    sortBtn.addEventListener('click', () => {
        const input = document.getElementById('arrayInput').value.trim();
        if (input) {
            sortArray('manual', input);
        } else {
            alert('Введите массив!');
        }
    });

    async function sortArray(type, arrayInput = '') {
        try {
            const data = type === 'manual' ?
                { type: 'manual', array: arrayInput.split(',').map(x => parseFloat(x.trim())) } :
                { type: 'random' };

            const response = await fetch('/sort', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.error) {
                alert('Ошибка: ' + result.error);
                return;
            }

            // Показываем результаты
            document.getElementById('originalArray').textContent = result.original.join(', ');
            document.getElementById('sortedArray').textContent = result.sorted.join(', ');
            document.getElementById('sortTime').textContent = result.time.toFixed(6);
            results.style.display = 'block';

            // Автоскролл
            results.scrollIntoView({ behavior: 'smooth' });

        } catch (error) {
            alert('Ошибка сортировки: ' + error.message);
        }
    }
});
