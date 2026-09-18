"use client";

import { useEffect, useRef, useState } from "react";

import * as THREE from "three";

export interface LivingBackdropOptions {
  /** Width divided by height of the source images. */
  aspect?: number;
  /** Inpainted plate with the subject removed. Revealed when the subject shifts. */
  backgroundSrc?: string;
  /** How far the subject swells, lifts and rocks with each breath (0 disables). */
  breath?: number;
  /** Seconds per breath. */
  breathPeriod?: number;
  /** Strength of the slow warp in the sky (0 disables). */
  clouds?: number;
  /** Number of floating dust motes (0 disables). */
  dust?: number;
  /** Depth value that stays still under parallax. Nearer moves one way, farther the other. */
  focus?: number;
  /** Strength of the pulsing sun glow (0 disables). */
  glow?: number;
  /** Where the glow sits in the image, from the top-left corner (0 to 1). */
  glowOrigin?: [number, number];
  /** Packed data map: R subject depth, G background depth, B subject mask. */
  mapsSrc?: string;
  /** Called when the canvas fails to start or a texture fails to load. */
  onError?: ((error: unknown) => void) | null;
  /** Called after the first frame is on screen. */
  onReady?: (() => void) | null;
  /** How far layers slide against each other, as a fraction of image width. */
  parallax?: number;
  /** Point the subject breathes around, from the top-left corner (0 to 1). Put it where the subject leaves the frame. */
  pivot?: [number, number];
  /** Cover-fit anchor with the same meaning as CSS object-position (0 to 1). */
  position?: [number, number];
  /** The untouched image. The subject layer is cut from it with the mask. */
  sceneSrc?: string;
  /** Canvas width in device pixels at or below which the small sources are used. */
  smallBelow?: number;
  /** Lighter variant of backgroundSrc for small screens. */
  smallBackgroundSrc?: string;
  /** Lighter variant of sceneSrc for small screens. */
  smallSceneSrc?: string;
  /** Strength of the wind in the near grass (0 disables). */
  wind?: number;
  /** Overscan so parallax never samples past the image edge. Match it on any poster underneath. */
  zoom?: number;
}

export const LIVING_BACKDROP_DEFAULTS: Required<LivingBackdropOptions> = {
  aspect: 1.5,
  backgroundSrc: "",
  breath: 1,
  breathPeriod: 4.6,
  clouds: 1,
  dust: 36,
  focus: 0.45,
  glow: 1,
  glowOrigin: [0, 0.28],
  mapsSrc: "",
  onError: null,
  onReady: null,
  parallax: 0.016,
  pivot: [0.92, 0],
  position: [0.5, 0.5],
  sceneSrc: "",
  smallBackgroundSrc: "",
  smallBelow: 1500,
  smallSceneSrc: "",
  wind: 1,
  zoom: 1.04,
};

export interface LivingBackdropInstance {
  destroy(): void;
  setOptions(next: LivingBackdropOptions): void;
}

const MAX_PIXEL_RATIO = 1.5;
const INTRO_SECONDS = 1.6;
const POINTER_DAMPING = 3.5;

const VERTEX_SHADER = /* glsl */ `
  varying vec2 vUv;

  void main() {
    vUv = uv;
    gl_Position = vec4(position.xy, 0.0, 1.0);
  }
`;

// Image coordinates run from the top-left corner, like CSS. Textures are
// uploaded unflipped to match, so a sample at (x, y) is the pixel you'd expect.
const FRAGMENT_SHADER = /* glsl */ `
  precision highp float;

  uniform sampler2D uScene;
  uniform sampler2D uBackground;
  uniform sampler2D uMaps;
  uniform vec2 uStart;
  uniform vec2 uSpan;
  uniform float uZoom;
  uniform float uAspect;
  uniform vec2 uPointer;
  uniform float uParallax;
  uniform float uFocus;
  uniform vec2 uPivot;
  uniform float uBreath;
  uniform float uSway;
  uniform float uTime;
  uniform float uWind;
  uniform float uClouds;
  uniform float uGlow;
  uniform vec2 uGlowOrigin;
  varying vec2 vUv;

  float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
  }

  float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(
      mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x),
      mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x),
      u.y
    );
  }

  void main() {
    vec2 screen = vec2(vUv.x, 1.0 - vUv.y);
    vec2 p = uStart + uSpan * (0.5 + (screen - 0.5) / uZoom);
    vec2 shift = uPointer * uParallax * vec2(1.0, uAspect);

    // Background. A few fixed-point steps find the source pixel whose own
    // depth lands it here, which keeps silhouettes from tearing.
    vec2 b = p;
    for (int i = 0; i < 3; i++) {
      b = p + shift * (texture2D(uMaps, b).g - uFocus);
    }
    float depth = texture2D(uMaps, b).g;

    float grass = smoothstep(0.55, 0.9, depth) * smoothstep(0.5, 0.85, p.y);
    float gust = noise(vec2(p.x * 5.0 + uTime * 0.35, p.y * 4.0));
    b.x += grass * uWind * (p.y - 0.45) *
      (sin(p.x * 55.0 + uTime * 1.7 + gust * 6.0) * 0.6 +
        sin(p.x * 23.0 - uTime * 1.1) * 0.4);

    float sky = smoothstep(0.2, 0.12, depth) * smoothstep(0.5, 0.3, p.y);
    b += sky * uClouds * vec2(
      sin(uTime * 0.11 + p.y * 9.0 + p.x * 3.0),
      0.4 * cos(uTime * 0.09 + p.x * 7.0)
    );

    vec3 color = texture2D(uBackground, b).rgb;

    vec2 toSun = (p - uGlowOrigin) * vec2(1.0, 1.0 / uAspect);
    float sun = exp(-length(toSun) * 2.6);
    color += vec3(1.0, 0.74, 0.42) * sun * uGlow *
      (0.5 + 0.5 * sin(uTime * 0.37));

    // Subject. Undo the breath around the pivot, then the parallax, to find
    // which source pixel ends up on this screen pixel.
    vec2 r = p - uPivot;
    r.y /= uAspect;
    r.y += 0.004 * uBreath;
    float angle = -(0.0075 * uBreath + 0.0025 * uSway);
    float c = cos(angle);
    float s = sin(angle);
    r = vec2(c * r.x - s * r.y, s * r.x + c * r.y) / (1.0 + 0.009 * uBreath);
    r.y *= uAspect;
    vec2 anchor = uPivot + r;

    vec2 h = anchor;
    for (int i = 0; i < 3; i++) {
      h = anchor + shift * (texture2D(uMaps, h).r - uFocus);
    }
    float mask = smoothstep(0.25, 0.75, texture2D(uMaps, h).b);
    vec3 subject = texture2D(uScene, h).rgb * (1.0 + 0.035 * uBreath);

    gl_FragColor = vec4(mix(color, subject, mask), 1.0);
  }
`;

const DUST_VERTEX_SHADER = /* glsl */ `
  attribute vec4 aSeed;
  uniform float uTime;
  uniform vec2 uPointer;
  uniform float uPixelRatio;
  uniform float uIntro;
  varying float vAlpha;

  void main() {
    float speed = 0.4 + aSeed.z;
    float rise = fract(aSeed.y + uTime * 0.008 * speed);
    float x = fract(
      aSeed.x + uTime * 0.003 * speed +
        0.02 * sin(uTime * 0.3 * speed + aSeed.w * 6.28)
    );
    float near = aSeed.w;
    vec2 pos = vec2(x, rise) * 2.0 - 1.0;
    pos -= uPointer * (0.01 + 0.05 * near);

    float twinkle = 0.6 + 0.4 * sin(uTime * (0.6 + aSeed.z) + aSeed.x * 40.0);
    vAlpha = twinkle * uIntro * (0.1 + 0.22 * near) *
      smoothstep(0.0, 0.15, rise) * smoothstep(1.0, 0.7, rise);

    gl_Position = vec4(pos, 0.0, 1.0);
    gl_PointSize = (1.5 + 4.5 * near) * uPixelRatio;
  }
`;

const DUST_FRAGMENT_SHADER = /* glsl */ `
  precision mediump float;
  varying float vAlpha;

  void main() {
    float d = length(gl_PointCoord - 0.5);
    float soft = smoothstep(0.5, 0.0, d);
    gl_FragColor = vec4(vec3(1.0, 0.86, 0.62) * soft * vAlpha, 1.0);
  }
`;

// Quick in, slow out, short rest. A plain sine reads as a machine.
function breathCurve(phase: number) {
  const ease = (t: number) => t * t * (3 - 2 * t);
  if (phase < 0.38) {
    return ease(phase / 0.38);
  }
  if (phase < 0.9) {
    return 1 - ease((phase - 0.38) / 0.52);
  }
  return 0;
}

function loadBitmapTexture(loader: THREE.ImageBitmapLoader, src: string) {
  return loader.loadAsync(src).then((bitmap) => {
    const texture = new THREE.Texture(bitmap);
    texture.generateMipmaps = false;
    texture.minFilter = THREE.LinearFilter;
    texture.magFilter = THREE.LinearFilter;
    texture.needsUpdate = true;
    return texture;
  });
}

export function createLivingBackdrop(
  { canvas }: { canvas: HTMLCanvasElement },
  options: LivingBackdropOptions = {}
): LivingBackdropInstance {
  const config = { ...LIVING_BACKDROP_DEFAULTS, ...options };

  const renderer = new THREE.WebGLRenderer({
    alpha: false,
    antialias: false,
    canvas,
    powerPreference: "low-power",
  });
  renderer.autoClear = false;

  const scene = new THREE.Scene();
  const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

  const material = new THREE.ShaderMaterial({
    depthTest: false,
    depthWrite: false,
    fragmentShader: FRAGMENT_SHADER,
    uniforms: {
      uAspect: { value: config.aspect },
      uBackground: { value: null },
      uBreath: { value: 0 },
      uClouds: { value: 0 },
      uFocus: { value: config.focus },
      uGlow: { value: 0 },
      uGlowOrigin: { value: new THREE.Vector2(...config.glowOrigin) },
      uMaps: { value: null },
      uParallax: { value: 0 },
      uPivot: { value: new THREE.Vector2(...config.pivot) },
      uPointer: { value: new THREE.Vector2() },
      uScene: { value: null },
      uSpan: { value: new THREE.Vector2(1, 1) },
      uStart: { value: new THREE.Vector2() },
      uSway: { value: 0 },
      uTime: { value: 0 },
      uWind: { value: 0 },
      uZoom: { value: config.zoom },
    },
    vertexShader: VERTEX_SHADER,
  });
  const geometry = new THREE.PlaneGeometry(2, 2);
  const quad = new THREE.Mesh(geometry, material);
  quad.frustumCulled = false;
  scene.add(quad);

  const dustMaterial = new THREE.ShaderMaterial({
    blending: THREE.AdditiveBlending,
    depthTest: false,
    depthWrite: false,
    fragmentShader: DUST_FRAGMENT_SHADER,
    transparent: true,
    uniforms: {
      uIntro: { value: 0 },
      uPixelRatio: { value: 1 },
      uPointer: material.uniforms.uPointer,
      uTime: material.uniforms.uTime,
    },
    vertexShader: DUST_VERTEX_SHADER,
  });
  let dust: THREE.Points | null = null;

  function buildDust() {
    if (dust) {
      scene.remove(dust);
      dust.geometry.dispose();
      dust = null;
    }
    const count = Math.max(Math.round(config.dust), 0);
    if (!count) {
      return;
    }
    const seeds = new Float32Array(count * 4);
    for (let i = 0; i < seeds.length; i++) {
      seeds[i] = Math.random();
    }
    const dustGeometry = new THREE.BufferGeometry();
    dustGeometry.setAttribute(
      "position",
      new THREE.BufferAttribute(new Float32Array(count * 3), 3)
    );
    dustGeometry.setAttribute("aSeed", new THREE.BufferAttribute(seeds, 4));
    dust = new THREE.Points(dustGeometry, dustMaterial);
    dust.frustumCulled = false;
    dust.renderOrder = 1;
    scene.add(dust);
  }

  let disposed = false;
  let ready = false;
  let loadToken = 0;
  let loadedKey = "";
  const textures: THREE.Texture[] = [];

  function clearTextures() {
    for (const texture of textures.splice(0)) {
      (texture.image as ImageBitmap | undefined)?.close?.();
      texture.dispose();
    }
  }

  function loadTextures() {
    const pr = Math.min(window.devicePixelRatio || 1, MAX_PIXEL_RATIO);
    const small = canvas.clientWidth * pr <= config.smallBelow;
    const sceneSrc = (small && config.smallSceneSrc) || config.sceneSrc;
    const backgroundSrc =
      (small && config.smallBackgroundSrc) || config.backgroundSrc;
    if (!(sceneSrc && backgroundSrc && config.mapsSrc)) {
      return;
    }
    const key = [sceneSrc, backgroundSrc, config.mapsSrc].join("|");
    if (key === loadedKey) {
      return;
    }
    loadedKey = key;
    loadToken += 1;
    const token = loadToken;

    const loader = new THREE.ImageBitmapLoader();
    loader.setOptions({
      colorSpaceConversion: "none",
      premultiplyAlpha: "none",
    });
    Promise.all(
      [sceneSrc, backgroundSrc, config.mapsSrc].map((src) =>
        loadBitmapTexture(loader, src)
      )
    ).then(
      (loaded) => {
        if (disposed || token !== loadToken) {
          for (const texture of loaded) {
            texture.dispose();
          }
          return;
        }
        clearTextures();
        textures.push(...loaded);
        const [sceneTexture, backgroundTexture, mapsTexture] = loaded;
        material.uniforms.uScene.value = sceneTexture;
        material.uniforms.uBackground.value = backgroundTexture;
        material.uniforms.uMaps.value = mapsTexture;
        ready = true;
      },
      (error) => {
        if (!disposed && token === loadToken) {
          loadedKey = "";
          config.onError?.(error);
        }
      }
    );
  }

  function resize() {
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    if (!(width && height)) {
      return;
    }
    const pr = Math.min(window.devicePixelRatio || 1, MAX_PIXEL_RATIO);
    renderer.setPixelRatio(pr);
    renderer.setSize(width, height, false);
    dustMaterial.uniforms.uPixelRatio.value = pr;

    // Same maths as object-fit: cover with object-position, so a poster
    // underneath lines up to the pixel.
    const ratio = width / height / config.aspect;
    const spanX = ratio < 1 ? ratio : 1;
    const spanY = ratio < 1 ? 1 : 1 / ratio;
    material.uniforms.uSpan.value.set(spanX, spanY);
    material.uniforms.uStart.value.set(
      (1 - spanX) * config.position[0],
      (1 - spanY) * config.position[1]
    );
  }

  function applyOptions() {
    material.uniforms.uAspect.value = config.aspect;
    material.uniforms.uFocus.value = config.focus;
    material.uniforms.uZoom.value = config.zoom;
    material.uniforms.uPivot.value.set(...config.pivot);
    material.uniforms.uGlowOrigin.value.set(...config.glowOrigin);
  }

  const observer = new ResizeObserver(() => {
    resize();
    loadTextures();
  });
  observer.observe(canvas);
  resize();
  buildDust();
  loadTextures();

  let inView = true;
  const viewObserver =
    typeof IntersectionObserver === "undefined"
      ? null
      : new IntersectionObserver((entries) => {
          inView = entries.at(-1)?.isIntersecting ?? true;
        });
  viewObserver?.observe(canvas);

  const pointerTarget = new THREE.Vector2();
  function onPointerMove(event: PointerEvent) {
    if (event.pointerType !== "mouse") {
      return;
    }
    pointerTarget.set(
      (event.clientX / window.innerWidth) * 2 - 1,
      (event.clientY / window.innerHeight) * 2 - 1
    );
  }
  window.addEventListener("pointermove", onPointerMove, { passive: true });

  function onContextLost(event: Event) {
    event.preventDefault();
    config.onError?.(new Error("WebGL context lost"));
  }
  canvas.addEventListener("webglcontextlost", onContextLost);

  let lastTime = 0;
  let elapsed = 0;
  let announced = false;

  function frame(delta: number) {
    elapsed += delta;

    // Everything eases in from rest, so the first frame is the still image
    // and the hand-off from a poster is invisible.
    const t = Math.min(elapsed / INTRO_SECONDS, 1);
    const intro = t * t * (3 - 2 * t);
    const uniforms = material.uniforms;
    uniforms.uTime.value = elapsed;
    uniforms.uParallax.value = config.parallax * intro;
    uniforms.uWind.value = 0.0028 * config.wind * intro;
    uniforms.uClouds.value = 0.003 * config.clouds * intro;
    uniforms.uGlow.value = 0.05 * config.glow * intro;
    uniforms.uBreath.value =
      breathCurve((elapsed / config.breathPeriod) % 1) * config.breath * intro;
    uniforms.uSway.value = Math.sin(elapsed * 0.43) * config.breath * intro;
    dustMaterial.uniforms.uIntro.value = intro;

    // A slow idle drift keeps the depth alive with no mouse (touch screens).
    const pointer = uniforms.uPointer.value as THREE.Vector2;
    const damping = 1 - Math.exp(-delta * POINTER_DAMPING);
    const driftX = Math.sin(elapsed * 0.23) * 0.3;
    const driftY = Math.sin(elapsed * 0.17 + 1.3) * 0.2;
    pointer.x += (pointerTarget.x + driftX - pointer.x) * damping;
    pointer.y += ((pointerTarget.y + driftY) * 0.6 - pointer.y) * damping;

    renderer.render(scene, camera);

    if (!announced) {
      announced = true;
      config.onReady?.();
    }
  }

  renderer.setAnimationLoop((time: number) => {
    if (!(inView && ready) || document.hidden) {
      lastTime = 0;
      return;
    }
    const delta = lastTime ? Math.min((time - lastTime) / 1000, 0.1) : 0;
    lastTime = time;
    frame(delta);
  });

  return {
    setOptions(next: LivingBackdropOptions) {
      const previousDust = config.dust;
      Object.assign(config, next);
      applyOptions();
      resize();
      loadTextures();
      if (config.dust !== previousDust) {
        buildDust();
      }
    },
    destroy() {
      disposed = true;
      loadToken += 1;
      renderer.setAnimationLoop(null);
      observer.disconnect();
      viewObserver?.disconnect();
      window.removeEventListener("pointermove", onPointerMove);
      canvas.removeEventListener("webglcontextlost", onContextLost);
      clearTextures();
      dust?.geometry.dispose();
      dustMaterial.dispose();
      geometry.dispose();
      material.dispose();
      renderer.dispose();
    },
  };
}

export interface LivingBackdropProps extends LivingBackdropOptions {
  className?: string;
  style?: React.CSSProperties;
}

/**
 * A still image brought to life: two depth-mapped layers that slide against
 * each other with the pointer, a subject that breathes, and ambient wind,
 * clouds, light and dust. Renders nothing visible until the first frame, and
 * nothing at all under prefers-reduced-motion, so put a poster underneath.
 * The canvas fills this element, so give it a position and a size.
 */
export function LivingBackdrop({
  className,
  style,
  ...options
}: LivingBackdropProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const instanceRef = useRef<LivingBackdropInstance | null>(null);
  const optionsRef = useRef(options);
  optionsRef.current = options;
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) {
      return;
    }
    const motionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");

    function start() {
      if (instanceRef.current || motionQuery.matches || !canvas) {
        return;
      }
      try {
        instanceRef.current = createLivingBackdrop(
          { canvas },
          {
            ...optionsRef.current,
            onError: (error) => {
              setVisible(false);
              optionsRef.current.onError?.(error);
            },
            onReady: () => {
              setVisible(true);
              optionsRef.current.onReady?.();
            },
          }
        );
      } catch (error) {
        optionsRef.current.onError?.(error);
      }
    }

    function stop() {
      instanceRef.current?.destroy();
      instanceRef.current = null;
      setVisible(false);
    }

    function onMotionChange() {
      if (motionQuery.matches) {
        stop();
      } else {
        start();
      }
    }

    start();
    motionQuery.addEventListener("change", onMotionChange);
    return () => {
      motionQuery.removeEventListener("change", onMotionChange);
      stop();
    };
  }, []);

  useEffect(() => {
    const { onError: _onError, onReady: _onReady, ...rest } = options;
    instanceRef.current?.setOptions(rest);
  });

  return (
    <div
      aria-hidden="true"
      className={className}
      style={{ overflow: "hidden", ...style }}
    >
      <canvas
        ref={canvasRef}
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
          display: "block",
          opacity: visible ? 1 : 0,
          transition: "opacity 700ms ease",
          pointerEvents: "none",
        }}
      />
    </div>
  );
}

export default LivingBackdrop;
