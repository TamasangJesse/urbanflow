pipeline {
    agent any

    

    stages {

        // ─────────────────────────────────────────────
        // STAGE 1: CHECKOUT
        // ─────────────────────────────────────────────
        stage('Checkout') {
            steps {
                echo '📥 Pulling latest code from GitHub...'
                checkout scm
            }
        }

        // ─────────────────────────────────────────────
        // STAGE 2: TEST (all 5 services in parallel)
        // ─────────────────────────────────────────────
        stage('Test') {
            parallel {

                stage('Test: user-service') {
                    steps {
                        dir('services/user-service') {
                            sh '''
                                pip install -r requirements.txt --quiet
                                pytest tests/ --cov=app --cov-report=xml --junitxml=test-results.xml -v
                            '''
                        }
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'services/user-service/test-results/*.xml'
                        }
                    }
                }

                stage('Test: incident-report-service') {
                    steps {
                        dir('services/incident-report-service') {
                            sh '''
                                pip install -r requirements.txt --quiet
                                pytest tests/ --cov=app --cov-report=xml --junitxml=test-results.xml -v
                            '''
                        }
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'services/incident-report-service/test-results/*.xml'
                        }
                    }
                }

                stage('Test: notification-service') {
                    steps {
                        dir('services/notification-service') {
                            sh '''
                                pip install -r requirements.txt --quiet
                                pytest tests/ --cov=app --cov-report=xml --junitxml=test-results.xml -v
                            '''
                        }
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'services/notification-service/test-results/*.xml'
                        }
                    }
                }

                stage('Test: traffic-intelligence-service') {
                    steps {
                        dir('services/traffic-intelligence-service') {
                            sh '''
                                pip install -r requirements.txt --quiet
                                pytest tests/ --cov=app --cov-report=xml --junitxml=test-results.xml -v
                            '''
                        }
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'services/traffic-intelligence-service/test-results/*.xml'
                        }
                    }
                }

                stage('Test: api-gateway') {
                    steps {
                        dir('services/api-gateway') {
                            sh '''
                                pip install -r requirements.txt --quiet
                                pytest tests/ --cov=app --cov-report=xml --junitxml=test-results.xml -v
                            '''
                        }
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'services/api-gateway/test-results/*.xml'
                        }
                    }
                }

            } // end parallel
        }   // end Test stage

        // ─────────────────────────────────────────────
        // STAGE 3: BUILD
        // ─────────────────────────────────────────────
        stage('Build') {
            steps {
                echo '🔨 Building all Docker images...'
                sh 'docker compose build'
            }
        }

        // ─────────────────────────────────────────────
        // STAGE 4: DEPLOY (main branch only)
        // ─────────────────────────────────────────────
        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                echo '🚀 Deploying UrbanFlow to production...'
                sh '''
                    docker compose down
                    docker compose up -d
                '''
            }
        }

    } // end stages

    // ─────────────────────────────────────────────
    // POST ACTIONS
    // ─────────────────────────────────────────────
    post {
        success {
            echo '✅ UrbanFlow deployed successfully'
        }
        failure {
            echo '❌ Pipeline failed — check test results'
        }
        always {
            echo "📊 Pipeline finished on branch: ${env.BRANCH_NAME}"
        }
    }

}