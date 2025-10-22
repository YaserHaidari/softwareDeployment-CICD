pipeline {
  agent any

  parameters {
    string(name: 'EC2_HOST', defaultValue: 'ubuntu@ec2-54-253-29-16.ap-southeast-2.compute.amazonaws.com', description: 'SSH target for deployment (user@host)')
    string(name: 'DOCKERHUB_USER', defaultValue: 'zerog123', description: 'Docker Hub username')
    string(name: 'IMAGE_NAME', defaultValue: 'python-flask-app', description: 'Image name')
    string(name: 'IMAGE_TAG', defaultValue: 'latest', description: 'Image tag')
  }

  environment {

    IMAGE = "${DOCKERHUB_USER}/${IMAGE_NAME}:${IMAGE_TAG}"
    LOCAL_IMAGE = "${IMAGE_NAME}:${IMAGE_TAG}"
  }

  stages {
    stage('Prepare') {
      steps {
        script {

          def resolvedTag = params.IMAGE_TAG == 'latest' ? env.BUILD_NUMBER : params.IMAGE_TAG
          env.IMAGE_TAG = resolvedTag


          def effective = env.DOCKER_BFLASK_IMAGE ?: "${params.DOCKERHUB_USER}/${params.IMAGE_NAME}:${resolvedTag}"
          env.EFFECTIVE_IMAGE = effective
          echo "Effective image will be: ${env.EFFECTIVE_IMAGE}"


          env.REG_CRED_ID = env.DOCKER_REGISTRY_CREDS ?: 'dockerhub'
          echo "Using registry credential id: ${env.REG_CRED_ID}"
        }
      }
    }
    stage('Lint') {
      steps {
        script {
          echo 'Running lint (flake8) inside python container'

          sh '''
            docker run --rm \
              -v "$WORKSPACE":/workspace \
              -w /workspace \
              python:3.12-slim \
              /bin/sh -c "python -m pip install --upgrade pip && pip install -r requirements.txt || true && pip install flake8 && flake8 --max-line-length=120"
          '''
        }
      }
    }
    stage('Build image') {
      steps {
        script {
          echo "Building ${env.EFFECTIVE_IMAGE}"
          sh "docker build -t ${env.EFFECTIVE_IMAGE} ."
        }
      }
    }

    stage('Push to Docker Hub') {
      steps {

        script {
          def cred = env.REG_CRED_ID ?: 'dockerhub'
          echo "Logging into registry with credentials id: ${cred}"
          withCredentials([usernamePassword(credentialsId: cred, usernameVariable: 'DH_USER', passwordVariable: 'DH_PW')]) {
            sh 'echo $DH_PW | docker login -u $DH_USER --password-stdin'
            sh "docker push ${env.EFFECTIVE_IMAGE}"
            // Verify the image is available in the registry by attempting a pull (will fail the stage if not)
            sh "docker pull ${env.EFFECTIVE_IMAGE} || (echo 'ERROR: verification pull failed for ${env.EFFECTIVE_IMAGE}' && exit 1)"
          }
        }
      }
    }

    stage('Deploy to EC2') {
      steps {

        withCredentials([sshUserPrivateKey(credentialsId: 'EC2_SSH', keyFileVariable: 'EC2_KEY', usernameVariable: 'EC2_USER')]) {

          script {
            def sshTarget = ''
            if (env.EC2_HOST?.contains('@')) {
              sshTarget = env.EC2_HOST
            } else {
              sshTarget = "${EC2_USER}@${EC2_HOST}"
            }
            env.SSH_TARGET = sshTarget
          }

          sh '''
            set -x
            ssh -i "$EC2_KEY" -o StrictHostKeyChecking=no -o BatchMode=yes -vvv "$SSH_TARGET" \
              "docker pull ${EFFECTIVE_IMAGE} && \
               docker stop ${IMAGE_NAME}-run || true && \
               docker rm ${IMAGE_NAME}-run || true && \
               docker run -d -p 5000:5000 --name ${IMAGE_NAME}-run ${EFFECTIVE_IMAGE}"
          '''
        }
      }
    }
  }

  post {
    success {
      echo "Deployment succeeded: ${IMAGE} deployed to ${EC2_HOST}"
    }
    failure {
      echo 'Deployment failed'
    }
  }
}