// Description: MathJax configuration file for Remark
// Documentation: math_syntax.txt

// The delimiters '', $, and $$ match those defined in Conversion.py.
// Therefore, to change the delimiters requires changing them here, and 
// to update Conversion.py correspondingly.

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

// This is needed because we forward the MathJax configuration 
// in each file to this configuration file.
MathJax.Hub.Configured();

