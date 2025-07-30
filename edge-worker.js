// Cloudflare Worker for edge processing without logs
addEventListener('fetch', event => {
    event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
    // CORS headers for GitHub Pages
    const corsHeaders = {
        'Access-Control-Allow-Origin': '*', // Update with your GitHub Pages URL in production
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, X-No-Track',
        'Access-Control-Max-Age': '86400',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'Referrer-Policy': 'no-referrer'
    }
    
    // Handle preflight requests
    if (request.method === 'OPTIONS') {
        return new Response(null, { 
            status: 204,
            headers: corsHeaders 
        })
    }
    
    // Only accept POST requests
    if (request.method !== 'POST') {
        return new Response(JSON.stringify({ 
            error: 'Method not allowed',
            allowed: ['POST']
        }), { 
            status: 405,
            headers: {
                ...corsHeaders,
                'Content-Type': 'application/json'
            }
        })
    }
    
    try {
        const { data, session } = await request.json()
        
        // Process the request without any logging
        const response = await processRequest(data, session)
        
        return new Response(JSON.stringify(response), {
            status: 200,
            headers: {
                ...corsHeaders,
                'Content-Type': 'application/json',
                'Cache-Control': 'no-store, no-cache, must-revalidate, private',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        })
    } catch (error) {
        // Return generic error without details
        return new Response(JSON.stringify({ 
            response: 'I can help you with that. Let me process this locally instead.',
            fallback: true,
            timestamp: Date.now()
        }), {
            status: 200, // Always 200 to avoid revealing errors
            headers: {
                ...corsHeaders,
                'Content-Type': 'application/json'
            }
        })
    }
}

async function processRequest(message, sessionId) {
    // Use KV storage for ephemeral session data (if available)
    const sessionKey = `session_${sessionId}`
    
    // Get session context if it exists
    let context = {}
    if (typeof AI_TUTOR_KV !== 'undefined') {
        const stored = await AI_TUTOR_KV.get(sessionKey, 'json')
        if (stored) {
            context = stored
        }
    }
    
    // Generate appropriate response
    const response = generateTutoringResponse(message, context)
    
    // Update context
    context.lastInteraction = Date.now()
    context.messageCount = (context.messageCount || 0) + 1
    
    // Store updated context (auto-expires after 24 hours)
    if (typeof AI_TUTOR_KV !== 'undefined') {
        await AI_TUTOR_KV.put(
            sessionKey, 
            JSON.stringify(context),
            { expirationTtl: 86400 } // 24 hours
        )
    }
    
    return {
        response: response,
        timestamp: Date.now(),
        processed: 'edge'
    }
}

function generateTutoringResponse(message, context) {
    const lower = message.toLowerCase()
    
    // Categorize the query
    if (lower.includes('help') || lower.includes('stuck')) {
        return generateGuidanceResponse(message, context)
    } else if (lower.includes('explain') || lower.includes('understand')) {
        return generateExplanationResponse(message, context)
    } else if (lower.includes('practice') || lower.includes('problem')) {
        return generatePracticeResponse(message, context)
    } else if (lower.includes('review') || lower.includes('study')) {
        return generateReviewResponse(message, context)
    } else {
        return generateGeneralResponse(message, context)
    }
}

function generateGuidanceResponse(message, context) {
    const responses = [
        "Let's work through this together. What specific part is giving you trouble?",
        "I can see you're working hard on this. Can you show me what you've tried so far?",
        "Good question! Instead of giving you the answer directly, let me guide you. What do you think the first step should be?",
        "That's a great problem to tackle. Let's break it down into smaller pieces. What do you understand so far?"
    ]
    
    return selectResponse(responses, context)
}

function generateExplanationResponse(message, context) {
    const responses = [
        "Let me help you understand this concept better. What do you already know about it?",
        "That's an important topic! Can you tell me which specific aspect you'd like me to clarify?",
        "I'll guide you to discover this yourself. What patterns or connections do you notice?",
        "Great question! Let's explore this step by step. What's your current understanding?"
    ]
    
    return selectResponse(responses, context)
}

function generatePracticeResponse(message, context) {
    const responses = [
        "Excellent! Practice is key to learning. What type of problems would you like to work on?",
        "I'm ready to help you practice. Should we start with something you're comfortable with or challenge yourself?",
        "Practice makes perfect! What difficulty level would work best for you right now?",
        "Let's do some practice problems together. What topic should we focus on?"
    ]
    
    return selectResponse(responses, context)
}

function generateReviewResponse(message, context) {
    const responses = [
        "Review is a great way to reinforce learning. What would you like to go over?",
        "Smart thinking! Regular review helps retention. Which topics shall we revisit?",
        "I'm here to help you review. What concepts do you want to strengthen?",
        "Let's review together. What material would you like to focus on?"
    ]
    
    return selectResponse(responses, context)
}

function generateGeneralResponse(message, context) {
    const responses = [
        "That's interesting! Can you tell me more about what you're working on?",
        "I'm here to help guide your learning. What would you like to explore?",
        "Good thinking! How can I assist you with this?",
        "I'd be happy to help. What aspect would you like to focus on?"
    ]
    
    return selectResponse(responses, context)
}

function selectResponse(responses, context) {
    // Use context to avoid repetition
    const lastIndex = context.lastResponseIndex || -1
    let newIndex
    
    do {
        newIndex = Math.floor(Math.random() * responses.length)
    } while (newIndex === lastIndex && responses.length > 1)
    
    context.lastResponseIndex = newIndex
    return responses[newIndex]
}

// Health check endpoint
async function handleHealthCheck() {
    return new Response(JSON.stringify({
        status: 'healthy',
        timestamp: Date.now(),
        mode: 'privacy-first'
    }), {
        headers: {
            'Content-Type': 'application/json'
        }
    })
}