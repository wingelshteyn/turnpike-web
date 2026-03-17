/**
 * Relaxing floating particles animation
 * Soft glowing dots that drift slowly across the screen
 */
(function () {
    var canvas = document.getElementById('particles');
    if (!canvas) return;

    var ctx = canvas.getContext('2d');
    var particles = [];
    var PARTICLE_COUNT = 150;
    var mouse = { x: -1000, y: -1000 };

    // Palette: teal, blue, amber, purple — matching the CSS orbs
    var colors = [
        { r: 20, g: 184, b: 166 },   // teal
        { r: 59, g: 130, b: 246 },    // blue
        { r: 245, g: 158, b: 11 },    // amber
        { r: 139, g: 92, b: 246 },    // purple
        { r: 16, g: 185, b: 129 },    // green
    ];

    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }

    function createParticle(forceY) {
        var color = colors[Math.floor(Math.random() * colors.length)];
        var size = Math.random() * 2.5 + 0.8;
        return {
            x: Math.random() * canvas.width,
            y: forceY !== undefined ? forceY : Math.random() * canvas.height,
            size: size,
            baseSize: size,
            color: color,
            alpha: Math.random() * 0.4 + 0.1,
            baseAlpha: Math.random() * 0.4 + 0.1,
            // Slow, gentle velocity — equal in all directions
            vx: (Math.random() - 0.5) * 0.3,
            vy: (Math.random() - 0.5) * 0.3,
            // Breathing: slow size/alpha oscillation
            breathSpeed: Math.random() * 0.008 + 0.003,
            breathOffset: Math.random() * Math.PI * 2,
            // Wobble: gentle sinusoidal horizontal drift
            wobbleAmp: Math.random() * 0.3 + 0.1,
            wobbleSpeed: Math.random() * 0.005 + 0.002,
            wobbleOffset: Math.random() * Math.PI * 2,
        };
    }

    function init() {
        resize();
        particles = [];
        for (var i = 0; i < PARTICLE_COUNT; i++) {
            particles.push(createParticle());
        }
    }

    var time = 0;

    function update() {
        time++;
        for (var i = 0; i < particles.length; i++) {
            var p = particles[i];

            // Breathing
            var breath = Math.sin(time * p.breathSpeed + p.breathOffset);
            p.alpha = p.baseAlpha + breath * 0.15;
            p.size = p.baseSize + breath * 0.6;

            // Wobble
            var wobble = Math.sin(time * p.wobbleSpeed + p.wobbleOffset) * p.wobbleAmp;

            p.x += p.vx + wobble;
            p.y += p.vy;

            // Subtle mouse repulsion (very gentle)
            var dx = p.x - mouse.x;
            var dy = p.y - mouse.y;
            var dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < 120 && dist > 0) {
                var force = (120 - dist) / 120 * 0.4;
                p.x += (dx / dist) * force;
                p.y += (dy / dist) * force;
            }

            // Wrap around screen edges
            if (p.x < -20) p.x = canvas.width + 20;
            if (p.x > canvas.width + 20) p.x = -20;
            if (p.y < -20) p.y = canvas.height + 20;
            if (p.y > canvas.height + 20) p.y = -20;
        }
    }

    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        for (var i = 0; i < particles.length; i++) {
            var p = particles[i];
            var c = p.color;

            // Soft glow
            var gradient = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.size * 4);
            gradient.addColorStop(0, 'rgba(' + c.r + ',' + c.g + ',' + c.b + ',' + (p.alpha * 0.8) + ')');
            gradient.addColorStop(0.4, 'rgba(' + c.r + ',' + c.g + ',' + c.b + ',' + (p.alpha * 0.3) + ')');
            gradient.addColorStop(1, 'rgba(' + c.r + ',' + c.g + ',' + c.b + ',0)');

            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size * 4, 0, Math.PI * 2);
            ctx.fillStyle = gradient;
            ctx.fill();

            // Bright core
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size * 0.6, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(' + c.r + ',' + c.g + ',' + c.b + ',' + Math.min(p.alpha * 1.8, 0.9) + ')';
            ctx.fill();
        }

        // Draw subtle connection lines between nearby particles
        ctx.lineWidth = 0.5;
        for (var i = 0; i < particles.length; i++) {
            for (var j = i + 1; j < particles.length; j++) {
                var a = particles[i];
                var b = particles[j];
                var dx = a.x - b.x;
                var dy = a.y - b.y;
                var dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 150) {
                    var lineAlpha = (1 - dist / 150) * 0.08;
                    ctx.beginPath();
                    ctx.moveTo(a.x, a.y);
                    ctx.lineTo(b.x, b.y);
                    ctx.strokeStyle = 'rgba(148, 163, 184, ' + lineAlpha + ')';
                    ctx.stroke();
                }
            }
        }
    }

    function loop() {
        update();
        draw();
        requestAnimationFrame(loop);
    }

    // Track mouse (throttled)
    var mouseTimer;
    document.addEventListener('mousemove', function (e) {
        if (!mouseTimer) {
            mouseTimer = setTimeout(function () {
                mouse.x = e.clientX;
                mouse.y = e.clientY;
                mouseTimer = null;
            }, 50);
        }
    });

    window.addEventListener('resize', function () {
        resize();
    });

    init();
    loop();
})();
