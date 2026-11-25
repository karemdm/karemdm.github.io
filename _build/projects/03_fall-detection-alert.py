PAGE = {'slug': 'fall-detection-alert',
 'title': 'Fall Detection Alert',
 'repo': 'https://github.com/karemdm/fall-detection-alert',
 'video': 'demo.mp4',
 'poster': 'poster.jpg',
 'stack': ['Python', 'Ultralytics YOLO11-pose', 'ByteTrack / BoT-SORT', 'OpenCV', 'NumPy', 'pytest'],
 'frames': ['step-1.jpg', 'step-2.jpg', 'step-3.jpg'],
 'more_demos': [{'video': 'demo-ice.mp4', 'poster': 'demo-ice.jpg'}],
 'trace': {'csv': '_build/data/fall-detection-alert-fall-05.csv',
           'vmax': 1.0,
           'vmin': -0.5,
           'angle_lines': [(45, '45° falling'), (60, '60° lying')],
           'vel_lines': [(0.8, '0.8 h/s')]},
 'en': {'summary': 'Rule-based fall detection on YOLO pose keypoints with multi-person tracking and a per-person state '
                   'machine. No training, runs on CPU.',
        'meta': ['Video analytics', 'CLI', 'AGPL-3.0'],
        'lede': 'Raises an alert about a second after a person ends up lying on the ground. YOLO pose keypoints and '
                'multi-person tracking feed a small state machine per person, driven by rules you can read: torso '
                'angle, body shape and hip speed. No training data, no GPU: it runs on a laptop CPU and explains every '
                'alert it raises.',
        'video_alt': 'Screen recording: the fall-alert command runs in a terminal while the preview window shows a '
                     'person walking, falling and the red FALL ALERT banner.',
        'video_caption': 'The command running end to end: live preview on top, log and events JSON below. Recorded on '
                         'a laptop CPU, with model loading and processing sped up. Footage: GMDCSA24 (MIT).',
        'stats': [('9 / 9', 'falls caught in the fall mix'),
                  ('0', 'false alerts on the test clips'),
                  ('~1 s', 'lying posture before the alert fires'),
                  ('0', 'training images')],
        'how_title': 'Pose keypoints in, explainable alerts out',
        'how_intro': 'Each frame goes through a pose model with a tracker, so every person keeps an ID. From the '
                     'shoulders and hips the pipeline computes three simple features, and a state machine per person '
                     'turns them into an alert only after a lying posture is held, which filters out bending, sitting '
                     'and quick crouches.',
        'pipeline_caption': 'Processing pipeline, from the video frame to the outputs',
        'pipeline': [('Video frame', ['any MP4 / camera clip', 'frame time t']),
                     ('YOLO11n-pose', ['+ ByteTrack IDs', 'box + 17 keypoints', 'per person']),
                     ('Keypoint gate', ['shoulders / hips', 'conf ≥ 0.5', 'else box only']),
                     ('Features', ['torso angle θ', 'aspect ratio w/h', 'hip velocity v']),
                     ('State machine', ['one per track', 'pose gate, id repair', 'time thresholds']),
                     ('Outputs', ['annotated MP4', 'events JSON', 'trace CSV'])],
        'states_intro': 'The state machine is what keeps false alarms down: a fall must be followed by a lying posture '
                        'held for one second before the alert fires, and the alert closes on its own when the person '
                        'stands up again.',
        'states_caption': 'Per-person state machine with the default thresholds',
        'states': [('UPRIGHT', 'var(--ok)', 'standing or walking'),
                   ('FALLING', 'var(--warn)', 'fast drop or tilt'),
                   ('FALLEN', 'var(--accent)', 'lying posture'),
                   ('ALERT', 'var(--accent)', 'event logged')],
        'edges': [('UPRIGHT', 'FALLING', ['v ≥ 0.8 h/s', 'or θ ≥ 45°'], 'fwd'),
                  ('FALLING', 'FALLEN', ['θ ≥ 60°', 'or w/h ≥ 1.2'], 'fwd'),
                  ('FALLEN', 'ALERT', ['held 1.0 s'], 'fwd'),
                  ('FALLING', 'UPRIGHT', ['no lying for 2 s'], 'back'),
                  ('ALERT', 'UPRIGHT', ['upright held 2 s'], 'back')],
        'features': [('Torso angle θ',
                      'Angle of the shoulder-to-hip line from vertical: about 0° standing, about 90° lying.'),
                     ('Aspect ratio w/h',
                      'Width over height of the person box; the fallback when shoulders or hips are hidden.'),
                     ('Hip velocity v',
                      'Downward speed of the hips in body heights per second, so it does not depend on distance to the '
                      'camera.')],
        'results_title': 'What the rules see during a fall',
        'trace_intro': 'The chart below is the real trace written by <code>--trace-csv</code> for the clip in the '
                       'demo. The torso angle jumps past 45° when the person goes down, the state moves to FALLEN '
                       'almost immediately, and the alert opens one second later, at 3.31 s.',
        'trace_caption': 'Feature trace of track #1 on GMDCSA24 fall-05, with the state shown as background bands',
        'trace_legend': {'angle': 'torso angle θ (degrees)', 'velocity': 'hip velocity v (body heights / s)'},
        'frames': ['1.2 s · upright, green box', '2.6 s · fallen, red box', '4.2 s · alert banner open'],
        'results_table': (['Run', 'Hits', 'Misses', 'False alerts', 'Alert delay'],
                          [['imgsz 1280, conf 0.30 (published run, current library versions)',
                            '<b>9 / 9</b>',
                            '0',
                            '0',
                            '1.5–2.6 s (one late hit at +4.0 s)'],
                           ['previous code (before the id-switch guard), same settings and library versions',
                            '7 / 9', '2', '0', 'not tabulated'],
                           ['imgsz 1280, conf 0.35 (earlier run, older library versions)', '8 / 9', '1', '0',
                            '1.5–2.6 s (one marginal hit at +4.2 s)'],
                           ['imgsz 640, conf 0.35 (earlier run, older library versions)', '6 / 9', '3', '0',
                            '1.5–2.4 s']]),
        'results_note': 'Fall mix: eight falls from GMDCSA24 (three people, day and night, side, forward and backward '
                        'falls) plus an outdoor fall in snow. The published run uses the library '
                        'versions pinned in constraints.txt; with the previous code those versions gave 7 / 9, '
                        'because a new person at a hard cut was stitched onto the previous person\'s open alert. '
                        'Own measurement on one compilation, not a validation.',
        'more_demos': [{'title': 'Harder footage: slips on ice',
                        'intro': 'Doorbell and handheld phone clips, small people, portrait video and snow. With '
                                 '<code>--model yolo26s-pose.pt --conf 0.20</code> (plus the pose gate and id-switch '
                                 'repair, both on by default), all three slips raise an alert, and each alert closes '
                                 'within 2 s of its person leaving the screen.',
                        'alt': 'Screen recording: fall-alert runs on three outdoor slips on ice; each fall gets a red '
                               'FALL ALERT banner.',
                        'caption': 'Recorded on a laptop CPU, processing sped up. Third-party footage from a public '
                                   'compilation of slips on ice.',
                        'table': (['Pose model', 'imgsz', 'conf', 'Alerts (3 falls)'],
                                  [['yolo11n-pose (default)', '640', '0.30', '1 / 3'],
                                   ['<b>yolo26s-pose</b>', '<b>640</b>', '<b>0.20</b>', '<b>3 / 3</b>'],
                                   ['yolo26s-pose', '1280', '0.20', '2 / 3'],
                                   ['yolo26m-pose', '640', '0.20', '1 / 3']]),
                        'note': 'Swapping in the newer yolo26s-pose was the biggest win on small, handheld footage: it '
                                'keeps a person lying on the ground in view far longer than the nano model.'}],
        'run_title': 'Three steps to try it',
        'run': [('install',
                 '',
                 {'Linux / macOS': 'git clone https://github.com/karemdm/fall-detection-alert.git\n'
                                   'cd fall-detection-alert\n'
                                   'python3 -m venv .venv\n'
                                   'source .venv/bin/activate\n'
                                   'pip install -r requirements.txt\n'
                                   'pip install -e .',
                  'Windows · PowerShell': 'git clone https://github.com/karemdm/fall-detection-alert.git\n'
                                          'cd fall-detection-alert\n'
                                          'python -m venv .venv\n'
                                          '.venv\\Scripts\\Activate.ps1\n'
                                          'pip install -r requirements.txt\n'
                                          'pip install -e .',
                  'Windows · cmd': 'git clone https://github.com/karemdm/fall-detection-alert.git\n'
                                   'cd fall-detection-alert\n'
                                   'python -m venv .venv\n'
                                   '.venv\\Scripts\\activate.bat\n'
                                   'pip install -r requirements.txt\n'
                                   'pip install -e .'}),
                ('run on a sample clip',
                 'fall-alert -i samples/gmdcsa24-s1-fall-05.mp4 -o outputs/fall-05.mp4 --events-json '
                 'outputs/fall-05.json'),
                ('small or distant people',
                 'fall-alert -i input.mp4 -o outputs/out.mp4 --imgsz 1280 --trace-csv outputs/trace.csv')],
        'decisions_title': 'Why it is built this way',
        'decisions': [('Rules instead of a trained classifier',
                       'Every threshold has a physical meaning and can be tuned from the CLI, and every alert can be '
                       'explained from the trace. No fall dataset is needed to start.'),
                      ('Confirmation time',
                       'An alert needs a lying posture held for 1.0 s, with short gaps tolerated. That removes alarms '
                       'from bending, tying shoes or sitting down quickly.'),
                      ('Velocity in body heights',
                       "Normalizing the hip speed by the person's height makes the same threshold work near and far "
                       'from the camera.'),
                      ('Graceful degradation',
                       'When shoulders or hips are not visible, the box aspect ratio takes over, so occlusion does not '
                       'silence the detector.'),
                      ('Objects are not people',
                       'A track can only fall after it showed a body pose (6 confident keypoints) in some frame. Bins, '
                       'coats and shadows detected as a person never do, so their wide boxes no longer raise alerts.'),
                      ('Repairing id switches',
                       'When a person falls the box goes from tall to wide and the tracker often starts a new id. A '
                       'new track that appears within one body height of a track lost moments ago continues its state '
                       'and alert, unless the lost track was upright or the newcomer is neither tilted nor wide, so a '
                       'new person walking in starts fresh.')]},
 'pt': {'summary': 'Detecção de quedas por regras sobre os pontos-chave de pose do YOLO, com rastreamento de várias '
                   'pessoas e máquina de estados por pessoa. Sem treino, roda em CPU.',
        'meta': ['Análise de vídeo', 'CLI', 'AGPL-3.0'],
        'lede': 'Gera um alerta cerca de um segundo depois de a pessoa ficar deitada no chão após uma queda. '
                'Pontos-chave de pose do YOLO e rastreamento de várias pessoas alimentam uma pequena máquina de '
                'estados por pessoa, guiada por regras legíveis: ângulo do tronco, formato do corpo e velocidade do '
                'quadril. Sem dados de treino e sem GPU: roda na CPU de um notebook e explica cada alerta que gera.',
        'video_alt': 'Gravação de tela: o comando fall-alert roda no terminal enquanto a janela de prévia mostra uma '
                     'pessoa andando, caindo e a faixa vermelha FALL ALERT.',
        'video_caption': 'O comando rodando de ponta a ponta: prévia ao vivo em cima, log e JSON de eventos embaixo. '
                         'Gravado na CPU de um notebook, com carregamento do modelo e processamento acelerados. '
                         'Imagens: GMDCSA24 (MIT).',
        'stats': [('9 / 9', 'quedas detectadas na compilação'),
                  ('0', 'alarmes falsos nos clipes de teste'),
                  ('~1 s', 'de postura deitada até o alerta disparar'),
                  ('0', 'imagens de treino')],
        'how_title': 'Entram pontos-chave de pose, saem alertas explicáveis',
        'how_intro': 'Cada quadro passa por um modelo de pose com rastreador, então cada pessoa mantém um ID. A partir '
                     'dos ombros e do quadril, o pipeline calcula três atributos simples, e uma máquina de estados por '
                     'pessoa só gera o alerta depois que a postura deitada se mantém, o que filtra abaixar, sentar e '
                     'agachar rapidamente.',
        'pipeline_caption': 'Pipeline de processamento, do quadro do vídeo às saídas',
        'pipeline': [('Quadro do vídeo', ['qualquer MP4 / câmera', 'tempo t do quadro']),
                     ('YOLO11n-pose', ['+ IDs do ByteTrack', 'caixa + 17 pontos', 'por pessoa']),
                     ('Filtro de pontos', ['ombros / quadril', 'conf ≥ 0,5', 'senão só a caixa']),
                     ('Atributos', ['ângulo do tronco θ', 'proporção l/a', 'velocidade v']),
                     ('Máquina de estados', ['uma por pessoa', 'filtro, reparo de ID', 'limiares de tempo']),
                     ('Saídas', ['MP4 anotado', 'JSON de eventos', 'CSV de traço'])],
        'states_intro': 'A máquina de estados é o que segura os alarmes falsos: depois da queda, a postura deitada '
                        'precisa durar um segundo para o alerta disparar, e o alerta se encerra sozinho quando a '
                        'pessoa se levanta.',
        'states_caption': 'Máquina de estados por pessoa, com os limiares padrão',
        'states': [('UPRIGHT', 'var(--ok)', 'em pé ou andando'),
                   ('FALLING', 'var(--warn)', 'queda rápida ou inclinação'),
                   ('FALLEN', 'var(--accent)', 'postura deitada'),
                   ('ALERT', 'var(--accent)', 'evento registrado')],
        'edges': [('UPRIGHT', 'FALLING', ['v ≥ 0,8 a/s', 'ou θ ≥ 45°'], 'fwd'),
                  ('FALLING', 'FALLEN', ['θ ≥ 60°', 'ou l/a ≥ 1,2'], 'fwd'),
                  ('FALLEN', 'ALERT', ['mantido 1,0 s'], 'fwd'),
                  ('FALLING', 'UPRIGHT', ['sem deitar por 2 s'], 'back'),
                  ('ALERT', 'UPRIGHT', ['em pé por 2 s'], 'back')],
        'features': [('Ângulo do tronco θ',
                      'Ângulo da linha ombro-quadril em relação à vertical: cerca de 0° em pé, cerca de 90° deitado.'),
                     ('Proporção l/a',
                      'Largura sobre altura da caixa da pessoa; é o recurso quando ombros ou quadril estão ocultos.'),
                     ('Velocidade do quadril v',
                      'Velocidade de descida do quadril em alturas do corpo por segundo, independente da distância até '
                      'a câmera.')],
        'results_title': 'O que as regras enxergam durante uma queda',
        'trace_intro': 'O gráfico abaixo é o traço real gravado com <code>--trace-csv</code> para o clipe da '
                       'demonstração. O ângulo do tronco passa de 45° quando a pessoa cai, o estado vai para FALLEN '
                       'quase na hora e o alerta abre um segundo depois, em 3,31 s.',
        'trace_caption': 'Traço dos atributos da pessoa #1 no clipe GMDCSA24 fall-05, com o estado como faixas de '
                         'fundo',
        'trace_legend': {'angle': 'ângulo do tronco θ (graus)', 'velocity': 'velocidade do quadril v (alturas / s)'},
        'frames': ['1,2 s · em pé, caixa verde', '2,6 s · caída, caixa vermelha', '4,2 s · faixa de alerta aberta'],
        'results_table': (['Execução', 'Acertos', 'Não detectadas', 'Alarmes falsos', 'Atraso do alerta'],
                          [['imgsz 1280, conf 0,30 (execução publicada, versões atuais das bibliotecas)',
                            '<b>9 / 9</b>',
                            '0',
                            '0',
                            '1,5–2,6 s (uma tardia em +4,0 s)'],
                           ['código anterior (antes da proteção contra troca de ID), mesmas configurações e versões',
                            '7 / 9', '2', '0', 'não tabelado'],
                           ['imgsz 1280, conf 0,35 (execução anterior, versões antigas das bibliotecas)', '8 / 9', '1',
                            '0', '1,5–2,6 s (uma marginal em +4,2 s)'],
                           ['imgsz 640, conf 0,35 (execução anterior, versões antigas das bibliotecas)', '6 / 9', '3',
                            '0', '1,5–2,4 s']]),
        'results_note': 'Compilação: oito quedas do GMDCSA24 (três pessoas, dia e noite, quedas laterais, para frente '
                        'e para trás) e uma queda externa na neve. A execução publicada usa as versões de '
                        'bibliotecas fixadas em constraints.txt; com o código anterior essas versões davam 7 / 9, '
                        'porque uma pessoa nova num corte brusco era ligada ao alerta aberto da pessoa anterior. '
                        'Medição própria em uma compilação, não é uma validação.',
        'more_demos': [{'title': 'Vídeos mais difíceis: escorregões no gelo',
                        'intro': 'Clipes de campainha e de celular na mão, pessoas pequenas, vídeo vertical e neve. '
                                 'Com <code>--model yolo26s-pose.pt --conf 0.20</code> (além do filtro por pose e do '
                                 'reparo de troca de ID, ambos ativos por padrão), os três escorregões geram alerta, e '
                                 'cada alerta se encerra até 2 s depois de a pessoa sair da tela.',
                        'alt': 'Gravação de tela: fall-alert roda em três escorregões no gelo; cada queda recebe a '
                               'faixa vermelha FALL ALERT.',
                        'caption': 'Gravado na CPU de um notebook, processamento acelerado. Imagens de terceiros, de '
                                   'uma compilação pública de escorregões no gelo.',
                        'table': (['Modelo de pose', 'imgsz', 'conf', 'Alertas (3 quedas)'],
                                  [['yolo11n-pose (padrão)', '640', '0,30', '1 / 3'],
                                   ['<b>yolo26s-pose</b>', '<b>640</b>', '<b>0,20</b>', '<b>3 / 3</b>'],
                                   ['yolo26s-pose', '1280', '0,20', '2 / 3'],
                                   ['yolo26m-pose', '640', '0,20', '1 / 3']]),
                        'note': 'Trocar para o modelo mais novo, o yolo26s-pose, foi o maior ganho em vídeos pequenos '
                                'e de celular: ele mantém a pessoa caída no chão detectada por muito mais tempo que o '
                                'modelo nano.'}],
        'run_title': 'Três passos para testar',
        'run': [('instalação',
                 '',
                 {'Linux / macOS': 'git clone https://github.com/karemdm/fall-detection-alert.git\n'
                                   'cd fall-detection-alert\n'
                                   'python3 -m venv .venv\n'
                                   'source .venv/bin/activate\n'
                                   'pip install -r requirements.txt\n'
                                   'pip install -e .',
                  'Windows · PowerShell': 'git clone https://github.com/karemdm/fall-detection-alert.git\n'
                                          'cd fall-detection-alert\n'
                                          'python -m venv .venv\n'
                                          '.venv\\Scripts\\Activate.ps1\n'
                                          'pip install -r requirements.txt\n'
                                          'pip install -e .',
                  'Windows · cmd': 'git clone https://github.com/karemdm/fall-detection-alert.git\n'
                                   'cd fall-detection-alert\n'
                                   'python -m venv .venv\n'
                                   '.venv\\Scripts\\activate.bat\n'
                                   'pip install -r requirements.txt\n'
                                   'pip install -e .'}),
                ('rodar num clipe de exemplo',
                 'fall-alert -i samples/gmdcsa24-s1-fall-05.mp4 -o outputs/fall-05.mp4 --events-json '
                 'outputs/fall-05.json'),
                ('pessoas pequenas ou distantes',
                 'fall-alert -i input.mp4 -o outputs/out.mp4 --imgsz 1280 --trace-csv outputs/trace.csv')],
        'decisions_title': 'Por que foi construído assim',
        'decisions': [('Regras em vez de um classificador treinado',
                       'Cada limiar tem significado físico e pode ser ajustado pela linha de comando, e cada alerta '
                       'pode ser explicado pelo traço. Não é preciso um dataset de quedas para começar.'),
                      ('Tempo de confirmação',
                       'O alerta exige a postura deitada por 1,0 s, tolerando pequenas interrupções. Isso elimina '
                       'alarmes ao abaixar, amarrar o sapato ou sentar rápido.'),
                      ('Velocidade em alturas do corpo',
                       'Normalizar a velocidade do quadril pela altura da pessoa faz o mesmo limiar funcionar perto ou '
                       'longe da câmera.'),
                      ('Degradação controlada',
                       'Quando ombros ou quadril não aparecem, a proporção da caixa assume, então a oclusão não '
                       'silencia o detector.'),
                      ('Objeto não é pessoa',
                       'Uma trilha só pode cair depois de mostrar uma pose de corpo (6 pontos-chave confiáveis) em '
                       'algum quadro. Lixeiras, casacos e sombras detectados como pessoa nunca mostram, então suas '
                       'caixas largas não geram mais alertas.'),
                      ('Reparo de troca de ID',
                       'Na queda a caixa passa de alta para larga e o rastreador costuma criar um ID novo. Uma trilha '
                       'nova que surge a até uma altura de corpo de outra perdida há pouco continua o estado e o '
                       'alerta dela, a menos que a perdida estivesse em pé ou a nova não seja inclinada nem larga, '
                       'então uma pessoa nova que entra começa do zero.')]}}
