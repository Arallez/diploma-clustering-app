// JavaScript для админки задач (Task) - конструктор тестов

(function() {
    // Используем делегирование событий для надежного перехвата кликов на кнопки "Показать/Скрыть"
    document.addEventListener('click', function(e) {
        var target = e.target;
        if (target && (target.classList.contains('collapse-toggle') || (target.id && target.id.match(/^fieldsetcollapser/)))) {
            e.preventDefault();
            e.stopPropagation();
            
            // Ищем соответствующий fieldset
            var fieldset = null;
            var toggleId = target.id;
            
            // Вариант 1: по ID (fieldsetcollapser0 -> fieldset-0)
            if (toggleId) {
                var match = toggleId.match(/fieldsetcollapser(\d+)/);
                if (match) {
                    var index = match[1];
                    fieldset = document.getElementById('fieldset-' + index) || 
                              document.getElementById('fieldset' + index);
                }
                // Специальная обработка для конструктора теста (может быть fieldsetcollapser2 или другой номер)
                if (!fieldset && toggleId.match(/fieldsetcollapser/)) {
                    // Ищем fieldset-quiz-constructor по всем fieldsets с collapse
                    var allCollapseFieldsets = document.querySelectorAll('fieldset.collapse');
                    for (var i = 0; i < allCollapseFieldsets.length; i++) {
                        if (allCollapseFieldsets[i].id === 'fieldset-quiz-constructor') {
                            fieldset = allCollapseFieldsets[i];
                            break;
                        }
                    }
                }
            }
            
            // Вариант 2: ищем по структуре DOM - кнопка в h2, fieldset - родитель h2
            if (!fieldset) {
                var h2 = target.closest('h2');
                if (h2 && h2.parentElement && h2.parentElement.tagName === 'FIELDSET') {
                    fieldset = h2.parentElement;
                }
            }
            
            // Вариант 3: ищем все fieldsets с классом collapse и берем по индексу
            if (!fieldset) {
                var allCollapseFieldsets = document.querySelectorAll('fieldset.collapse');
                if (toggleId) {
                    var match = toggleId.match(/fieldsetcollapser(\d+)/);
                    if (match && allCollapseFieldsets[parseInt(match[1], 10)]) {
                        fieldset = allCollapseFieldsets[parseInt(match[1], 10)];
                    }
                }
            }
            
            // Переключаем collapsed класс
            if (fieldset) {
                var isCollapsed = fieldset.classList.contains('collapsed');
                if (isCollapsed) {
                    fieldset.classList.remove('collapsed');
                    target.textContent = 'Скрыть';
                } else {
                    fieldset.classList.add('collapsed');
                    target.textContent = 'Показать';
                }
            }
        }
    }, true); // Используем capture phase для перехвата до Django

    // Конструктор тестов
    var container = document.getElementById('quiz-questions-container');
    var addQuestionBtn = document.getElementById('add-quiz-question');
    if (!container || !addQuestionBtn) return;

    function nextQuestionIndex() {
        return container.querySelectorAll('.quiz-question-block').length;
    }

    function escapeAttr(s) {
        if (s == null) return '';
        return String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    function makeOptionRow(qIdx, oIdx, idVal, textVal) {
        var tr = document.createElement('tr');
        tr.className = 'quiz-option-row';
        tr.innerHTML = '<td><input type="text" name="quiz_option_' + qIdx + '_' + oIdx + '_id" value="' + escapeAttr(idVal) + '" maxlength="10" style="width:50px"></td>' +
            '<td><input type="text" name="quiz_option_' + qIdx + '_' + oIdx + '_text" value="' + escapeAttr(textVal) + '" style="width:100%"></td>' +
            '<td><button type="button" class="deletelink remove-quiz-option">×</button></td>';
        tr.querySelector('.remove-quiz-option').addEventListener('click', function() {
            var tbody = tr.closest('tbody');
            if (tbody.querySelectorAll('.quiz-option-row').length > 1) {
                tr.remove();
                reindexOptionsInTbody(tbody);
            }
        });
        return tr;
    }

    function reindexOptionsInTbody(tbody) {
        var qIdx = parseInt(tbody.getAttribute('data-question-index'), 10);
        var rows = tbody.querySelectorAll('.quiz-option-row');
        rows.forEach(function(tr, idx) {
            var idInp = tr.querySelector('input[name$="_id"]');
            var textInp = tr.querySelector('input[name$="_text"]');
            if (idInp) idInp.name = 'quiz_option_' + qIdx + '_' + idx + '_id';
            if (textInp) textInp.name = 'quiz_option_' + qIdx + '_' + idx + '_text';
        });
    }

    function addQuestionBlock(qIdx) {
        var block = document.createElement('fieldset');
        block.className = 'module aligned quiz-question-block';
        block.setAttribute('data-question-index', qIdx);
        block.innerHTML = '<h3 style="margin-top:0">Вопрос ' + (qIdx + 1) + '</h3>' +
            '<div class="form-row"><label>Текст вопроса:</label><textarea name="quiz_question_' + qIdx + '" rows="2" style="width:100%; max-width:600px"></textarea></div>' +
            '<div class="form-row"><label>Варианты ответа:</label>' +
            '<table class="quiz-options-table" style="width:100%; max-width:700px; border-collapse:collapse">' +
            '<thead><tr><th style="width:60px">ID</th><th>Текст</th><th style="width:40px"></th></tr></thead>' +
            '<tbody class="quiz-options-tbody" data-question-index="' + qIdx + '"></tbody></table>' +
            '<p><button type="button" class="addlink add-quiz-option" data-question-index="' + qIdx + '">Добавить вариант</button></p></div>' +
            '<div class="form-row"><label>Правильный ответ (ID):</label><input type="text" name="quiz_correct_' + qIdx + '" value="" maxlength="10" style="width:80px"></div>' +
            '<p><button type="button" class="deletelink remove-quiz-question">Удалить вопрос</button></p>';
        container.appendChild(block);
        var tbody = block.querySelector('.quiz-options-tbody');
        tbody.appendChild(makeOptionRow(qIdx, 0, 'a', ''));
        tbody.appendChild(makeOptionRow(qIdx, 1, 'b', ''));
        block.querySelector('.remove-quiz-question').addEventListener('click', function() {
            if (container.querySelectorAll('.quiz-question-block').length > 1) {
                block.remove();
                reindexQuestionBlocks();
            }
        });
        block.querySelector('.add-quiz-option').addEventListener('click', function() {
            var tbody = block.querySelector('.quiz-options-tbody');
            var oIdx = tbody.querySelectorAll('.quiz-option-row').length;
            tbody.appendChild(makeOptionRow(qIdx, oIdx, String.fromCharCode(97 + Math.min(oIdx, 25)), ''));
            reindexOptionsInTbody(tbody);
        });
    }

    function reindexQuestionBlocks() {
        container.querySelectorAll('.quiz-question-block').forEach(function(block, newIdx) {
            block.setAttribute('data-question-index', newIdx);
            block.querySelector('h3').textContent = 'Вопрос ' + (newIdx + 1);
            var qText = block.querySelector('textarea[name^="quiz_question_"]');
            var qCorrect = block.querySelector('input[name^="quiz_correct_"]');
            if (qText) qText.name = 'quiz_question_' + newIdx;
            if (qCorrect) qCorrect.name = 'quiz_correct_' + newIdx;
            var tbody = block.querySelector('.quiz-options-tbody');
            tbody.setAttribute('data-question-index', newIdx);
            reindexOptionsInTbody(tbody);
            var addOptBtn = block.querySelector('.add-quiz-option');
            if (addOptBtn) addOptBtn.setAttribute('data-question-index', newIdx);
        });
    }

    addQuestionBtn.addEventListener('click', function() {
        addQuestionBlock(nextQuestionIndex());
    });

    container.querySelectorAll('.quiz-question-block').forEach(function(block) {
        block.querySelectorAll('.remove-quiz-option').forEach(function(btn) {
            btn.addEventListener('click', function() {
                var tr = btn.closest('tr');
                var tbody = tr.closest('tbody');
                if (tbody.querySelectorAll('.quiz-option-row').length > 1) {
                    tr.remove();
                    reindexOptionsInTbody(tbody);
                }
            });
        });
        var addOptBtn = block.querySelector('.add-quiz-option');
        if (addOptBtn) {
            addOptBtn.addEventListener('click', function() {
                var tbody = block.querySelector('.quiz-options-tbody');
                var qIdx = parseInt(tbody.getAttribute('data-question-index'), 10);
                var oIdx = tbody.querySelectorAll('.quiz-option-row').length;
                tbody.appendChild(makeOptionRow(qIdx, oIdx, String.fromCharCode(97 + Math.min(oIdx, 25)), ''));
                reindexOptionsInTbody(tbody);
            });
        }
        block.querySelectorAll('.remove-quiz-question').forEach(function(btn) {
            btn.addEventListener('click', function() {
                if (container.querySelectorAll('.quiz-question-block').length > 1) {
                    block.remove();
                    reindexQuestionBlocks();
                }
            });
        });
    });
})();
