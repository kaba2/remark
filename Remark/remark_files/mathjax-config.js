// Description: MathJax configuration file for Remark
// Documentation: math_syntax.txt

MathJax.Hub.Config({
    asciimath2jax: 
    {
        delimiters: [["''", "''"]],
        // Disable MathJax on all class-names...
        ignoreClass: '.*',
        // ... except on 'ascii-math'.
        processClass: 'ascii-math'
    },
    tex2jax: 
    {   
        inlineMath: [["$","$"]],
        displayMath: [["$$", "$$"]],
        processEscapes: true,
        // Disable MathJax on all class-names...
        ignoreClass: '.*',
        // ... except on 'latex-math'.
        processClass: 'latex-math'
    }
});
MathJax.Hub.Configured();

