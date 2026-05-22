pipeline {
    agent any

    environment {
        IMAGE_NAME = 'bloodbank-app'
        IMAGE_TAG  = "${BUILD_NUMBER}"
        REGISTRY   = 'mohak0039'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
                echo "Source checked out from branch: ${env.BRANCH_NAME}"
            }
        }

        stage('Build') {
            steps {
                bat "docker build -f app/Dockerfile -t ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} ."
                bat "docker tag ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} ${REGISTRY}/${IMAGE_NAME}:latest"
                echo "Image built: ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
            }
        }

        stage('Test') {
            steps {
                bat "docker run --rm -e FLASK_ENV=testing ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} python -m pytest tests/ -v --tb=short"
            }
        }

        stage('Push Image') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-credentials',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    bat "docker login -u %DOCKER_USER% -p %DOCKER_PASS%"
                    bat "docker push ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
                    bat "docker push ${REGISTRY}/${IMAGE_NAME}:latest"
                }
                echo "Image pushed: ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
            }
        }

        stage('Deploy') {
            steps {
                bat "docker-compose down --remove-orphans & exit /B 0"
                bat "docker-compose up -d"
                bat "docker-compose ps"
                echo "Application deployed on port 5000"
            }
        }

    }

    post {
        always {
            bat "docker logout & exit /B 0"
        }
        success {
            echo "Pipeline succeeded for build #${BUILD_NUMBER}"
        }
        failure {
            echo "Pipeline FAILED for build #${BUILD_NUMBER}. Check logs above."
        }
    }
}
