pipeline {
    agent any

    environment {
        IMAGE_NAME = "aceest-fitness"
        IMAGE_TAG  = "${BUILD_NUMBER}"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
                echo "Source checked out from ${env.GIT_URL} (branch: ${env.GIT_BRANCH})"
            }
        }

        stage('Setup Python Environment') {
            steps {
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Lint') {
            steps {
                sh '''
                    . .venv/bin/activate
                    flake8 app.py \
                        --count \
                        --select=E9,F63,F7,F82 \
                        --show-source \
                        --statistics
                '''
            }
        }

        stage('Unit Tests') {
            steps {
                sh '''
                    . .venv/bin/activate
                    export DB_PATH=/tmp/jenkins_test_${BUILD_NUMBER}.db
                    pytest tests/test_app.py -v --tb=short
                '''
            }
            post {
                always {
                    // Archive test results if junit plugin is available
                    junit allowEmptyResults: true, testResults: '**/test-results/*.xml'
                }
            }
        }

        stage('Docker Build') {
            steps {
                sh "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} ."
                echo "Docker image ${IMAGE_NAME}:${IMAGE_TAG} built successfully"
            }
        }

        stage('Docker Test') {
            steps {
                sh """
                    docker run --rm \
                        -e DB_PATH=/tmp/docker_test.db \
                        ${IMAGE_NAME}:${IMAGE_TAG} \
                        python -m pytest tests/test_app.py -v --tb=short
                """
            }
        }

        stage('Smoke Test') {
            steps {
                sh """
                    docker run -d --name aceest-smoke-${BUILD_NUMBER} \
                        -p 5001:5000 \
                        -e DB_PATH=/tmp/smoke.db \
                        ${IMAGE_NAME}:${IMAGE_TAG}
                    sleep 5
                    curl -sf http://localhost:5001/health || \
                        (docker stop aceest-smoke-${BUILD_NUMBER}; exit 1)
                    docker stop aceest-smoke-${BUILD_NUMBER}
                    docker rm  aceest-smoke-${BUILD_NUMBER}
                """
            }
        }
    }

    post {
        success {
            echo "BUILD ${BUILD_NUMBER} PASSED – ACEest image ${IMAGE_NAME}:${IMAGE_TAG} is ready."
        }
        failure {
            echo "BUILD ${BUILD_NUMBER} FAILED – check the console output above."
        }
        always {
            // Clean workspace to avoid disk bloat on the Jenkins agent
            cleanWs()
        }
    }
}
