// Description: MathJax configuration file for Remark
// Documentation: math_syntax.txt

// We disable MathJax's delimiter-based detection of mathematics.
// Instead, we provide the MathJax <script> elements directly.
// For example, for inline latex math, we provide
//
// <script class="latex-math" type="math/tex">ax^2 + bx^2 + c = 0</script>

MathJax.Hub.Config({
    config: 
    [
        "MMLorHTML.js"
    ],
    jax: 
    [
        "input/TeX",
        //"input/MathML",
        "input/AsciiMath",
        "output/HTML-CSS",
        "output/NativeMML", 
        "output/CommonHTML"
    ],
    extensions: 
    [
        "tex2jax.js",
        //"mml2jax.js",
        "asciimath2jax.js",
        "MathMenu.js",
        "MathZoom.js", 
        "CHTML-preview.js"
    ],
    TeX: 
    {
        extensions: 
        [
            "AMSmath.js",
            "AMSsymbols.js",
            "noErrors.js",
            "noUndefined.js"
        ],
        equationNumbers: 
        { 
            autoNumber: "AMS" 
        }    
    },
    asciimath2jax: 
    {
        // Disable delimiter-based detection.
        delimiters: [],
        // Disable MathJax on all class-names...
        ignoreClass: 'remark-all',
        // ... except on AsciiMath spans.
        processClass: 'ascii-math'
    },
    tex2jax: 
    {
        // Disable delimiter-based detection.
        inlineMath: [],
        displayMath: [],
        // Disable MathJax on all class-names...
        ignoreClass: 'remark-all',
        // ... except on Latex math spans.
        processClass: 'latex-math|display-latex-math'
    }
});

// This is needed because we forward the MathJax configuration 
// in each file to this configuration file.
MathJax.Hub.Configured();

